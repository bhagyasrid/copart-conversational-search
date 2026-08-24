import assert from "node:assert/strict";
import test from "node:test";
import {correctSearchText,emptyFilters,filterLabels,inventory,searchVehicles,shouldClarifySearchIntent,updateFilters} from "../app/search.ts";

const parse=(...messages)=>messages.reduce((filters,message)=>updateFilters(message,filters),emptyFilters());

test("provides 200 vehicles with seller context",()=>{assert.equal(inventory.length,200);assert.ok(inventory.every(vehicle=>vehicle.saleReason.length>20));assert.ok(inventory.every(vehicle=>vehicle.damageSeverity>=0&&vehicle.damageSeverity<=100));assert.ok(inventory.every(vehicle=>vehicle.imageUrl.startsWith("https://upload.wikimedia.org/")));assert.equal(new Set(inventory.map(vehicle=>`${vehicle.make}|${vehicle.model}|${vehicle.imageUrl}`)).size,56);assert.equal(new Set(inventory.map(vehicle=>vehicle.imageUrl)).size,56);assert.equal(new Set(inventory.map(vehicle=>vehicle.lot)).size,200);});

test("builds and refines a multi-turn Toyota SUV search",()=>{
  const filters=parse("Show SUVs in Texas","Only Toyota","2020 or newer","Under $25k");
  assert.deepEqual(filters.bodies,["SUV"]);assert.deepEqual(filters.makes,["Toyota"]);assert.deepEqual(filters.states,["TX"]);assert.equal(filters.minYear,2020);assert.equal(filters.maxPrice,25000);assert.ok(searchVehicles(filters).every(v=>v.make==="Toyota"&&v.body==="SUV"&&v.state==="TX"&&v.year>=2020&&v.price<=25000));
});

test("minimum price replaces a conflicting maximum",()=>{
  const filters=parse("Toyota SUVs under $25k","Actually above $25k");
  assert.equal(filters.minPrice,25000);assert.equal(filters.maxPrice,undefined);assert.match(filterLabels(filters).join(" "),/Above \$25k/);
});

test("supports alternatives and exclusions",()=>{
  const filters=parse("Toyota or Honda SUVs","No flood damage");
  assert.deepEqual(filters.makes,["Toyota","Honda"]);assert.deepEqual(filters.excludedDamages,["Flood"]);assert.ok(searchVehicles(filters).every(v=>["Toyota","Honda"].includes(v.make)&&v.body==="SUV"&&v.damage!=="Flood"));
});

test("supports ranges, powertrain, location, and sorting",()=>{
  const filters=parse("Electric or hybrid AWD SUVs between $15k and $40k in California","Sort by lowest price");
  assert.deepEqual(filters.fuels,["Hybrid","Electric"]);assert.deepEqual(filters.drives,["AWD"]);assert.deepEqual(filters.states,["CA"]);assert.equal(filters.minPrice,15000);assert.equal(filters.maxPrice,40000);const results=searchVehicles(filters);for(let i=1;i<results.length;i++)assert.ok(results[i-1].price<=results[i].price);
});

test("reset clears all accumulated constraints",()=>{
  const filters=parse("Ford trucks in Texas","Reset search");
  assert.deepEqual(filters,emptyFilters());assert.equal(searchVehicles(filters).length,200);
});

test("show all cars clears a previous filtered search",()=>{
  const filters=parse("Electric SUVs under $35k","Show all cars available");
  assert.deepEqual(filters,emptyFilters());assert.equal(searchVehicles(filters).length,200);
});

test("explicit new-search language clears old context before applying new criteria",()=>{
  const initial=parse("black sedans under $50k");
  for(const query of ["New search: SUVs under $40k","Start over with SUVs under $40k","Instead, find SUVs under $40k"]){
    const filters=updateFilters(query,initial);
    assert.deepEqual(filters.bodies,["SUV"]);assert.equal(filters.maxPrice,40000);
    assert.deepEqual(filters.colors,[]);assert.ok(searchVehicles(filters).every(vehicle=>vehicle.body==="SUV"&&vehicle.price<=40000));
  }
  const refinement=updateFilters("make it SUVs under $40k",initial);
  assert.deepEqual(refinement.colors,["Black"]);
});

test("a standalone vehicle-category change starts a fresh search",()=>{
  const initial=parse("black SUVs under $30k");
  const fresh=updateFilters("sedan under $40k",initial);
  assert.deepEqual(fresh.bodies,["Sedan"]);assert.equal(fresh.maxPrice,40000);assert.deepEqual(fresh.colors,[]);
  const refinement=updateFilters("make it a sedan under $40k",initial);
  assert.deepEqual(refinement.bodies,["Sedan"]);assert.equal(refinement.maxPrice,40000);assert.deepEqual(refinement.colors,["Black"]);
});

test("asks for intent when a new car request could retain prior filters",()=>{
  const hybrid=parse("give hybrid cars");
  assert.equal(shouldClarifySearchIntent("give black cars",hybrid),true);
  assert.equal(shouldClarifySearchIntent("Toyota",hybrid),true);
  assert.equal(shouldClarifySearchIntent("sedans",hybrid),true);
  assert.equal(shouldClarifySearchIntent("Toyota RAV4 XLE",hybrid),true);
  assert.equal(shouldClarifySearchIntent("only black cars",hybrid),false);
  assert.equal(shouldClarifySearchIntent("switch to Toyota",hybrid),false);
  assert.equal(shouldClarifySearchIntent("new search: black cars",hybrid),false);
  assert.equal(shouldClarifySearchIntent("give black cars",emptyFilters()),false);
});

test("supports exact years, year ranges, and expanded vehicle attributes",()=>{
  let filters=updateFilters("2025 model",emptyFilters());
  assert.equal(filters.minYear,2025);assert.equal(filters.maxYear,2025);
  filters=updateFilters("hybrid SUVs from 2019 to 2023",emptyFilters());
  assert.equal(filters.minYear,2019);assert.equal(filters.maxYear,2023);
  filters=updateFilters("automobile, gasoline, 4 cylinder, made in Japan",emptyFilters());
  assert.deepEqual(filters.vehicleTypes,["Automobile"]);assert.deepEqual(filters.fuels,["Gas"]);
  assert.deepEqual(filters.cylinders,[4]);assert.deepEqual(filters.manufacturedIn,["Japan"]);
  assert.ok(searchVehicles(filters).every(v=>v.vehicleType==="Automobile"&&v.fuel==="Gas"&&v.cylinders===4&&v.manufacturedIn==="Japan"));
});

test("corrects common search typos and treats after a year as exclusive",()=>{
  assert.match(correctSearchText("toyato hybird sedna"),/toyota hybrid sedan/i);
  assert.match(correctSearchText("Toytoa hybrdi transmision manufctured milage belwo"),/toyota hybrid transmission manufactured mileage below/i);
  const filters=updateFilters("i want a sedna under 30000, toyato after 2025",emptyFilters());
  assert.deepEqual(filters.makes,["Toyota"]);assert.deepEqual(filters.bodies,["Sedan"]);
  assert.equal(filters.maxPrice,30000);assert.equal(filters.minYear,2026);assert.equal(filters.maxYear,undefined);
  assert.equal(searchVehicles(filters).length,0);
});

test("enforces below-50k as a current-bid ceiling, including typos",()=>{
  for(const query of ["below 50k","belo 50k","belwo 50k","under $50,000","less than 50k"]){
    const filters=updateFilters(query,emptyFilters());const results=searchVehicles(filters);
    assert.equal(filters.maxPrice,50000);assert.ok(results.length>0);
    assert.ok(results.every(vehicle=>vehicle.price<=50000));
  }
});
