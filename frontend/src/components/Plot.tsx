import {lazy, Suspense} from 'react';
import type {ComponentProps} from 'react';
import type ReactPlot from 'react-plotly.js';
import {LoadingState} from './shared';

const LazyPlot = lazy(() => import('./PlotImpl').then(module => ({default: module.Plot})));
type PlotProps = ComponentProps<typeof ReactPlot>;

export function Plot(props: PlotProps) {
  return <Suspense fallback={<LoadingState/>}><LazyPlot {...props}/></Suspense>;
}
