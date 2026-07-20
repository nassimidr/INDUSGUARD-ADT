import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {afterEach,beforeEach,describe,expect,it,vi} from 'vitest';
import {VisionPage} from './VisionPage';

const socketState=vi.hoisted(()=>({listener:undefined as ((event:MessageEvent)=>void)|undefined}));
vi.mock('../services/websocket',()=>({DashboardSocket:class{connect(listener:(event:MessageEvent)=>void){socketState.listener=listener}close(){}}}));

const health={enabled:true,mode:'demo',loaded:true,available:true,custom_model_loaded:true,technical_fallback:false,model_name:'yolov8n',model_version:'phase8a-v1',device:'cpu',detail:null};
const detection={detection_id:'vision-det-1',equipment_id:'CONVEYOR-001',camera_id:'camera_01',frame_id:'frame_1',defect_type:'obstacle',confidence:.91,timestamp:'2026-07-20T10:00:00Z',trace_id:'trace-1',original_image_path:'data/vision/demo/a.png',annotated_image_path:'outputs/vision/annotated/a.jpg',model_name:'yolov8n',model_version:'phase8a-v1'};

function response(data:unknown){return Promise.resolve({ok:true,status:200,json:async()=>({data,meta:{}})} as Response)}
function mockApi(detections:unknown[]=[],healthValue={...health}){return vi.fn((input:RequestInfo|URL,init?:RequestInit)=>{const url=String(input);if(url.includes('/vision/health'))return response(healthValue);if(url.includes('/vision/analyze')&&init?.method==='POST')return response({trace_id:'trace-new',frame_id:'frame-new',detections:[detection],inference_time_ms:2,custom_model_loaded:true,technical_fallback:false});return response(detections)})}
function renderPage(){const client=new QueryClient({defaultOptions:{queries:{retry:false},mutations:{retry:false}}});return render(<QueryClientProvider client={client}><VisionPage/></QueryClientProvider>)}

describe('VisionPage',()=>{
  beforeEach(()=>{vi.stubGlobal('fetch',mockApi());socketState.listener=undefined});
  afterEach(()=>{cleanup();vi.unstubAllGlobals()});

  it('rend la page Vision',async()=>{renderPage();expect(screen.getByText('Vision industrielle')).toBeInTheDocument();expect(await screen.findByText(/yolov8n/)).toBeInTheDocument()});
  it('affiche l’état vide',async()=>{renderPage();expect(await screen.findByText('Aucune détection visuelle')).toBeInTheDocument()});
  it('affiche une détection et ses images',async()=>{vi.stubGlobal('fetch',mockApi([detection]));renderPage();expect(await screen.findByText(/obstacle · 91.0/)).toBeInTheDocument();expect(screen.getByAltText('Original frame_1')).toBeInTheDocument();expect(screen.getByAltText('Annotée frame_1')).toBeInTheDocument()});
  it('signale explicitement le fallback',async()=>{vi.stubGlobal('fetch',mockApi([],{...health,custom_model_loaded:false,technical_fallback:true}));renderPage();expect(await screen.findByText('Fallback technique uniquement')).toBeInTheDocument();expect(screen.getByText(/fallback COCO ne valide/)).toBeInTheDocument()});
  it('applique le filtre de classe',async()=>{const fetchMock=mockApi();vi.stubGlobal('fetch',fetchMock);renderPage();await screen.findByText('Aucune détection visuelle');fireEvent.mouseDown(screen.getByLabelText('Classe'));fireEvent.click(await screen.findByText('obstacle'));await waitFor(()=>expect(fetchMock.mock.calls.some(call=>String(call[0]).includes('defect_type=obstacle'))).toBe(true))});
  it('affiche une erreur API',async()=>{vi.stubGlobal('fetch',vi.fn(()=>Promise.reject(new Error('vision offline'))));renderPage();expect((await screen.findAllByText('vision offline')).length).toBeGreaterThan(0)});
  it('rafraîchit après un événement WebSocket',async()=>{const fetchMock=mockApi();vi.stubGlobal('fetch',fetchMock);renderPage();await screen.findByText('Aucune détection visuelle');const before=fetchMock.mock.calls.filter(call=>String(call[0]).includes('/vision/detections')).length;socketState.listener?.({data:JSON.stringify({event:'vision.detection.created',data:detection})} as MessageEvent);await waitFor(()=>expect(fetchMock.mock.calls.filter(call=>String(call[0]).includes('/vision/detections')).length).toBeGreaterThan(before))});
  it('lance une analyse de démonstration',async()=>{const fetchMock=mockApi();vi.stubGlobal('fetch',fetchMock);renderPage();await screen.findByText('Aucune détection visuelle');fireEvent.click(screen.getByRole('button',{name:'Analyser'}));expect(await screen.findByText(/Analyse terminée/)).toBeInTheDocument();expect(fetchMock.mock.calls.some(call=>String(call[0]).includes('/vision/analyze')&&call[1]?.method==='POST')).toBe(true)});
});
