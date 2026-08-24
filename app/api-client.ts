import {correctSearchText,Filters,updateFilters} from "./search";

const apiUrl=process.env.NEXT_PUBLIC_SEARCH_API_URL?.replace(/\/$/,"");

export async function refineFilters(query:string,current:Filters):Promise<Filters>{
  const correctedQuery=correctSearchText(query);
  try{
    const endpoint=apiUrl?`${apiUrl}/v1/search/refine`:"/api/refine";
    const response=await fetch(endpoint,{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({query:correctedQuery,current_filters:current})});
    if(!response.ok)throw new Error(`Search service returned ${response.status}`);
    const payload=await response.json() as {filters:Filters};
    // Re-apply explicit, deterministic constraints after AI interpretation so
    // numeric bounds such as "below 50k" can never be weakened by the model.
    return updateFilters(correctedQuery,payload.filters);
  }catch{
    // The public demo stays fully usable when the optional API is unavailable.
    return updateFilters(correctedQuery,current);
  }
}
