import type {ApiEnvelope} from '../types';
const API='/api/v1';
export async function request<T>(path:string,init?:RequestInit):Promise<ApiEnvelope<T>>{const response=await fetch(`${API}${path}`,{...init,headers:{'Content-Type':'application/json',...init?.headers}});if(!response.ok)throw new Error(`API ${response.status}`);return response.json() as Promise<ApiEnvelope<T>>}
export const api={get:<T>(path:string)=>request<T>(path),patch:<T>(path:string,body?:unknown)=>request<T>(path,{method:'PATCH',body:body?JSON.stringify(body):undefined}),post:<T>(path:string,body?:unknown)=>request<T>(path,{method:'POST',body:body?JSON.stringify(body):undefined})};
