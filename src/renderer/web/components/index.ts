import CompleteMarginals from './CompleteMarginals.js';
import NumericSourceGraph from './NumericSourceGraph.js';
import MetricHorizon from './MetricHorizon.js';
import PackedSource from './PackedSource.js';
import SourceGraph from './SourceGraph.js';
import SourceCompact from './SourceCompact.js';
import type {ComponentType} from 'react';
import type {Card,Rect} from './primitives.js';
import QuantileContrast from './QuantileContrast.js';
import PairedObservations from './PairedObservations.js';
import EvidenceInventory from './EvidenceInventory.js';
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
import MembershipMatrix from './MembershipMatrix.js';
import AnomalyOnset from './AnomalyOnset.js';
import RelationshipPairs from './RelationshipPairs.js';
import DeploymentGroups from './DeploymentGroups.js';
import ScopeMatrix from './ScopeMatrix.js';
import ScopeTiles from './ScopeTiles.js';
import DiagnosticMatrix from './DiagnosticMatrix.js';
import DiagnosticCompact from './DiagnosticCompact.js';
import LiteralText from './LiteralText.js';
import RequestJointScatter from './RequestJointScatter.js';
import RequestPairMarginals from './RequestPairMarginals.js';
import PopulationProfile from './PopulationProfile.js';
export const components:Record<string,ComponentType<{card:Card;rect:Rect}>>={
  'trace_joint.complete_marginals':CompleteMarginals,
  'metric_horizon.source_compact':MetricHorizon,
  'metric_packed.source_compact':PackedSource,
  'trace_packed.source_compact':PackedSource,
  'log_packed.source_compact':PackedSource,
  'inventory_packed.source_compact':PackedSource,
  'comparison_packed.source_compact':PackedSource,

  'graph.numeric_source':NumericSourceGraph,
  'graph.source_compact':SourceGraph,
  'metric.source_compact':SourceCompact,
  'trace.source_compact':SourceCompact,
  'log.source_compact':SourceCompact,
  'inventory.source_compact':SourceCompact,
  'comparison.source_compact':SourceCompact,
  'contrast.quantile_contrast':QuantileContrast,
  'comparison.paired':PairedObservations,
  'inventory.identities':EvidenceInventory,
  'metric.line':MetricLine,'metric.time_bars':MetricTimeBars,'metric.heatmap':MetricHeatmap,
  'trace.paired_bars':TracePairedBars,'trace.dumbbell':TraceDumbbell,'trace.table':TraceTable,
  'log.timeline':LogTimeline,'log.table':LogTable,'graph.node_link':RelationshipGraph,'graph.matrix':RelationshipMatrix,'graph.membership_matrix':MembershipMatrix,
  'events.onset':AnomalyOnset,'graph.edge_pairs':RelationshipPairs,'graph.deployment_groups':DeploymentGroups,
  'scope.matrix':ScopeMatrix,'scope.tiles':ScopeTiles,'diagnostic.matrix':DiagnosticMatrix,'diagnostic.compact':DiagnosticCompact,
  'literal.text':LiteralText,'trace_joint.scatter':RequestJointScatter,'trace_joint.marginals':RequestPairMarginals,'trace_profile.quantiles':PopulationProfile
};
