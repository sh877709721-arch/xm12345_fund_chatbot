import{y as s,ad as o,t as r}from"./index-DYldXMee.js";/**
 * @license lucide-react v0.542.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const c=[["path",{d:"M5 12h14",key:"1ays0h"}]],h=s("minus",c);/**
 * @license lucide-react v0.542.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const p=[["path",{d:"M17 14V2",key:"8ymqnk"}],["path",{d:"M9 18.12 10 14H4.17a2 2 0 0 1-1.92-2.56l2.33-8A2 2 0 0 1 6.5 2H20a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-2.76a2 2 0 0 0-1.79 1.11L12 22a3.13 3.13 0 0 1-3-3.88Z",key:"m61m77"}]],m=s("thumbs-down",p);/**
 * @license lucide-react v0.542.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const d=[["path",{d:"M7 10v12",key:"1qc93n"}],["path",{d:"M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2a3.13 3.13 0 0 1 3 3.88Z",key:"emmmcr"}]],_=s("thumbs-up",d),g={GOOD:"good",MEDIUM:"medium",BAD:"bad"};async function u(t){try{return(await o.get(`/v1/vote/message/${t}`)).data}catch(e){return e.response?.status===404?(console.log(`消息 ${t} 没有投票记录`),null):(console.error("获取投票信息失败:",e),null)}}async function v(t,e,n){try{const a=await o.post("/v1/vote/",{message_id:t,vote_type:e,feedback:n});return r.success("投票成功"),a.data}catch(a){throw r.error(a.response?.data?.detail||a.message||"投票失败"),a}}async function y(t={}){try{const e=new URLSearchParams;return e.append("page",(t.page||1).toString()),e.append("size",(t.size||10).toString()),t.vote_type&&e.append("vote_type",t.vote_type),t.start_date&&e.append("start_date",t.start_date),t.end_date&&e.append("end_date",t.end_date),(await o.get(`/v1/vote/with_messages?${e.toString()}`)).data}catch(e){throw console.error("获取投票统计失败:",e),e}}export{h as M,_ as T,g as V,m as a,y as b,v as c,u as g};
