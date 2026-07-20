import React from 'react';
import {useMutation,useQuery,useQueryClient} from '@tanstack/react-query';
import {Alert,Box,Button,CardMedia,MenuItem,Stack,TextField,Typography} from '@mui/material';
import {api} from '../services/api';
import {DashboardSocket} from '../services/websocket';
import type {VisionDetection,VisionHealth,VisionInferenceResponse} from '../types';
import {EmptyState,ErrorState,LoadingState,PageGrid,PageHeader,SectionCard,StatusChip} from '../components/shared';

const defectClasses=['belt_misalignment','obstacle','material_accumulation'];
const demoImages=['sample_belt_misalignment.png','sample_obstacle.png','sample_material_accumulation.png','sample_normal.png'];

export function VisionPage(){
  const client=useQueryClient();
  const [equipment,setEquipment]=React.useState('CONVEYOR-001');
  const [defect,setDefect]=React.useState('');
  const [start,setStart]=React.useState('');
  const [end,setEnd]=React.useState('');
  const [image,setImage]=React.useState(demoImages[0]);
  const params=new URLSearchParams({page_size:'100'});if(equipment)params.set('equipment_id',equipment);if(defect)params.set('defect_type',defect);if(start)params.set('start',start);if(end)params.set('end',end);
  const health=useQuery({queryKey:['vision-health'],queryFn:()=>api.get<VisionHealth>('/vision/health'),refetchInterval:5000});
  const detections=useQuery({queryKey:['vision-detections',params.toString()],queryFn:()=>api.get<VisionDetection[]>(`/vision/detections?${params}`),refetchInterval:5000});
  const analyze=useMutation({mutationFn:()=>api.post<VisionInferenceResponse>('/vision/analyze',{image_path:`data/vision/demo/${image}`,equipment_id:equipment,camera_id:'camera_01'}),onSuccess:()=>client.invalidateQueries({queryKey:['vision-detections']})});
  React.useEffect(()=>{const socket=new DashboardSocket();socket.connect(event=>{try{const message=JSON.parse(event.data);if(message.event==='vision.detection.created'||message.event==='vision.analysis.failed')client.invalidateQueries({queryKey:['vision-detections']})}catch{/* malformed events are ignored by the view */}});return()=>socket.close()},[client]);
  return <><PageHeader title="Vision industrielle" subtitle="Détection locale de défauts visuels — Phase 8A"/>
    {health.isLoading?<LoadingState/>:health.error?<ErrorState message={health.error.message}/>:<PageGrid>
      <SectionCard title="État du modèle"><Stack sx={{gap:1}}><StatusChip value={health.data?.data.available?'ready':'unavailable'}/><Typography>{health.data?.data.model_name} · {health.data?.data.model_version}</Typography><Typography>Mode {health.data?.data.mode} · {health.data?.data.device}</Typography></Stack></SectionCard>
      <SectionCard title="Poids industriels"><Stack sx={{gap:1}}><StatusChip value={health.data?.data.custom_model_loaded?'custom':'fallback'}/><Typography>{health.data?.data.custom_model_loaded?'Modèle personnalisé chargé':'Fallback technique uniquement'}</Typography></Stack></SectionCard>
    </PageGrid>}
    {health.data?.data.technical_fallback&&<Alert severity="warning" sx={{mt:2}}>Le fallback COCO ne valide aucune classe industrielle et ses classes ne sont pas remappées.</Alert>}
    <Box sx={{mt:2}}><SectionCard title="Démonstration sans caméra"><Stack direction={{xs:'column',md:'row'}} sx={{gap:2}}>
      <TextField select label="Image de démonstration" value={image} onChange={event=>setImage(event.target.value)} sx={{minWidth:260}}>{demoImages.map(value=><MenuItem key={value} value={value}>{value}</MenuItem>)}</TextField>
      <TextField select label="Équipement" value={equipment} onChange={event=>setEquipment(event.target.value)} sx={{minWidth:200}}>{['CONVEYOR-001','MOTOR-001','BEARING-001','PUMP-001'].map(value=><MenuItem key={value} value={value}>{value}</MenuItem>)}</TextField>
      <Button variant="contained" disabled={analyze.isPending} onClick={()=>analyze.mutate()}>{analyze.isPending?'Analyse…':'Analyser'}</Button>
    </Stack>{analyze.error&&<Alert severity="error" sx={{mt:2}}>{analyze.error.message}</Alert>}{analyze.data&&<Alert severity="success" sx={{mt:2}}>Analyse terminée : {analyze.data.data.detections.length} détection(s), trace {analyze.data.data.trace_id}</Alert>}</SectionCard></Box>
    <Box sx={{mt:2}}><SectionCard title="Filtres"><Stack direction={{xs:'column',md:'row'}} sx={{gap:2}}>
      <TextField select label="Classe" value={defect} onChange={event=>setDefect(event.target.value)} sx={{minWidth:220}}><MenuItem value="">Toutes</MenuItem>{defectClasses.map(value=><MenuItem key={value} value={value}>{value}</MenuItem>)}</TextField>
      <TextField label="Depuis" type="date" value={start} onChange={event=>setStart(event.target.value)} slotProps={{inputLabel:{shrink:true}}}/><TextField label="Jusqu'au" type="date" value={end} onChange={event=>setEnd(event.target.value)} slotProps={{inputLabel:{shrink:true}}}/>
    </Stack></SectionCard></Box>
    <Box sx={{mt:2}}>{detections.isLoading?<LoadingState/>:detections.error?<ErrorState message={detections.error.message}/>:!detections.data?.data.length?<EmptyState label="Aucune détection visuelle"/>:<Stack sx={{gap:2}}>{detections.data.data.map(item=><SectionCard key={item.detection_id} title={`${item.defect_type} · ${(item.confidence*100).toFixed(1)} %`}><Stack direction={{xs:'column',lg:'row'}} sx={{gap:2}}><CardMedia component="img" image={`/api/v1/vision/detections/${item.detection_id}/image/original`} alt={`Original ${item.frame_id}`} sx={{maxWidth:360,borderRadius:1}}/>{item.annotated_image_path&&<CardMedia component="img" image={`/api/v1/vision/detections/${item.detection_id}/image/annotated`} alt={`Annotée ${item.frame_id}`} sx={{maxWidth:360,borderRadius:1}}/>}<Stack sx={{gap:1}}><Typography>{item.equipment_id} · {item.camera_id}</Typography><Typography>{item.timestamp}</Typography><Typography>Trace : {item.trace_id}</Typography><Typography>Modèle : {item.model_name} · {item.model_version}</Typography></Stack></Stack></SectionCard>)}</Stack>}</Box>
  </>
}
