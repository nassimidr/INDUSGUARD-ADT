import {Box,Card,CardContent,Chip,CircularProgress,Paper,Stack,Table,TableBody,TableCell,TableContainer,TableHead,TableRow,Typography} from '@mui/material';
import type {ReactNode} from 'react';
import type {RecordRow} from '../types';
export function PageHeader({title,subtitle,actions}:{title:string;subtitle:string;actions?:ReactNode}){return <Stack direction={{xs:'column',md:'row'}} sx={{justifyContent:'space-between',gap:2,mb:3}}><Box><Typography variant="h4">{title}</Typography><Typography color="text.secondary">{subtitle}</Typography></Box>{actions}</Stack>}
export function KpiCard({label,value,accent='#39d0c4'}:{label:string;value:ReactNode;accent?:string}){return <Card><CardContent><Typography color="text.secondary" variant="body2">{label}</Typography><Typography variant="h4" sx={{mt:1,color:accent}}>{value}</Typography></CardContent></Card>}
export function StatusChip({value}:{value:string|boolean|null|undefined}){const text=String(value??'inconnu');const positive=['healthy','ready','completed','normal','low','true'].includes(text.toLowerCase());return <Chip size="small" label={text} color={positive?'success':text==='critical'?'error':'warning'} variant="outlined"/>}
export function EmptyState({label='Aucune donnée disponible'}:{label?:string}){return <Paper sx={{p:5,textAlign:'center'}}><Typography color="text.secondary">{label}</Typography></Paper>}
export function LoadingState(){return <Box sx={{display:'grid',minHeight:240,placeItems:'center'}}><CircularProgress/></Box>}
export function ErrorState({message}:{message:string}){return <Paper sx={{p:3,borderColor:'error.main'}}><Typography color="error">{message}</Typography></Paper>}
export function DataTable({rows,columns}:{rows:RecordRow[];columns:string[]}){if(!rows.length)return <EmptyState/>;return <TableContainer component={Paper}><Table size="small"><TableHead><TableRow>{columns.map(c=><TableCell key={c}>{c.replaceAll('_',' ')}</TableCell>)}</TableRow></TableHead><TableBody>{rows.map((row,i)=><TableRow key={String(row.id??i)} hover>{columns.map(c=><TableCell key={c}>{c==='status'||c==='level'||c==='priority'||c==='risk_level'?<StatusChip value={String(row[c]??'')}/>:String(row[c]??'—')}</TableCell>)}</TableRow>)}</TableBody></Table></TableContainer>}
export function SectionCard({title,children}:{title:string;children:ReactNode}){return <Card><CardContent><Typography variant="h6" sx={{mb:2}}>{title}</Typography>{children}</CardContent></Card>}
export function LiveIndicator(){return <Stack direction="row" sx={{gap:1,alignItems:'center'}}><Box sx={{width:8,height:8,borderRadius:'50%',bgcolor:'success.main',boxShadow:'0 0 12px #4caf50'}}/><Typography variant="caption">TEMPS RÉEL</Typography></Stack>}
export const MetricValue=({children}:{children:ReactNode})=><Typography variant="h5">{children}</Typography>;
export const EquipmentBadge=({id}:{id:string})=><Chip label={id} size="small" color="primary" variant="outlined"/>;
export const PriorityBadge=({priority}:{priority:string})=><StatusChip value={priority}/>;
export const RiskBadge=({risk}:{risk:string})=><StatusChip value={risk}/>;
export const AgentBadge=({agent}:{agent:string})=><Chip label={agent.split('@')[0]} size="small"/>;
export const Timestamp=({value}:{value:string|null})=><span>{value?new Date(value).toLocaleString('fr-FR'):'—'}</span>;
export const HealthBar=({value=0}:{value?:number|null})=><Box sx={{height:7,borderRadius:4,bgcolor:'action.hover',overflow:'hidden'}}><Box sx={{width:`${Math.max(0,Math.min(100,value??0))}%`,height:'100%',bgcolor:(value??0)>70?'success.main':'warning.main'}}/></Box>;
export const Cost=({value}:{value:number|null})=><span>{new Intl.NumberFormat('fr-FR',{style:'currency',currency:'EUR'}).format(value??0)}</span>;
export const CountBadge=({value}:{value:number})=><Chip label={value} size="small"/>;
export const Panel=({children}:{children:ReactNode})=><Paper sx={{p:2}}>{children}</Paper>;
export const ToolbarSpacer=()=> <Box sx={{flex:1}}/>;
export const Mono=({children}:{children:ReactNode})=><Box component="code" sx={{fontFamily:'ui-monospace',fontSize:12}}>{children}</Box>;
export const DividerLabel=({children}:{children:ReactNode})=><Typography variant="overline" color="text.secondary">{children}</Typography>;
export const Trend=({value}:{value:number})=><Typography color={value>=0?'success.main':'error.main'}>{value>=0?'↑':'↓'} {Math.abs(value)}%</Typography>;
export const SeverityDot=({severity}:{severity:string})=><Box title={severity} sx={{width:10,height:10,borderRadius:'50%',bgcolor:severity==='critical'?'error.main':'warning.main'}}/>;
export const JsonPreview=({value}:{value:unknown})=><Box component="pre" sx={{overflow:'auto',fontSize:11}}>{JSON.stringify(value,null,2)}</Box>;
export const TimelineItem=({title,time}:{title:string;time:string})=><Stack direction="row" sx={{gap:2}}><SeverityDot severity="info"/><Box><Typography>{title}</Typography><Typography variant="caption" color="text.secondary">{time}</Typography></Box></Stack>;
export const ConnectionBadge=({connected}:{connected:boolean})=><StatusChip value={connected?'connecté':'hors ligne'}/>;
export const PageGrid=({children}:{children:ReactNode})=><Box sx={{display:'grid',gridTemplateColumns:{xs:'1fr',md:'repeat(2,1fr)',xl:'repeat(4,1fr)'},gap:2}}>{children}</Box>;
export const ChartShell=({children}:{children:ReactNode})=><Box sx={{height:330}}>{children}</Box>;
export const FilterBar=({children}:{children:ReactNode})=><Paper sx={{p:2,mb:2}}><Stack direction="row" sx={{gap:2}}>{children}</Stack></Paper>;
export const TitleWithBadge=({title,count}:{title:string;count:number})=><Stack direction="row" sx={{gap:1,alignItems:'center'}}><Typography variant="h6">{title}</Typography><CountBadge value={count}/></Stack>;
export const AppVersion=()=> <Typography variant="caption" color="text.secondary">Phase 7 · v7.0.0</Typography>;
