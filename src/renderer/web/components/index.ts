import type {ComponentType} from 'react';
import type {Card,Rect} from './primitives.js';
import MetricLine from './MetricLine.js';
import MetricTimeBars from './MetricTimeBars.js';
import MetricHeatmap from './MetricHeatmap.js';
import TracePairedBars from './TracePairedBars.js';
import TraceDumbbell from './TraceDumbbell.js';
import TraceTable from './TraceTable.js';
import LogTimeline from './LogTimeline.js';
import LogTable from './LogTable.js';
import RelationshipGraph from './RelationshipGraph.js';
import RelationshipMatrix from './RelationshipMatrix.js';
import AnomalyOnset from './AnomalyOnset.js';
import RelationshipPairs from './RelationshipPairs.js';
import DeploymentGroups from './DeploymentGroups.js';
export const components:Record<string,ComponentType<{card:Card;rect:Rect}>>={
  'metric.line':MetricLine,'metric.time_bars':MetricTimeBars,'metric.heatmap':MetricHeatmap,
  'trace.paired_bars':TracePairedBars,'trace.dumbbell':TraceDumbbell,'trace.table':TraceTable,
  'log.timeline':LogTimeline,'log.table':LogTable,'graph.node_link':RelationshipGraph,'graph.matrix':RelationshipMatrix,
  'events.onset':AnomalyOnset,'graph.edge_pairs':RelationshipPairs,'graph.deployment_groups':DeploymentGroups
};
