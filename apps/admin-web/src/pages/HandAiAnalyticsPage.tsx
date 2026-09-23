import React, { useState } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Chip,
  LinearProgress,
  Divider,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableRow,
} from '@mui/material';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import PhotoLibraryIcon from '@mui/icons-material/PhotoLibrary';
import FormatListNumberedIcon from '@mui/icons-material/FormatListNumbered';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import StorageIcon from '@mui/icons-material/Storage';
import { AdminTopbar } from '../components/layout/AdminTopbar';

// Mock session trend data (Session vs Recognition Confidence Score)
const CONFIDENCE_TREND = [
  { session: 1, confidence: 89.2, lines: 8 },
  { session: 2, confidence: 91.5, lines: 8 },
  { session: 3, confidence: 90.8, lines: 7 },
  { session: 4, confidence: 93.4, lines: 8 },
  { session: 5, confidence: 92.1, lines: 9 },
  { session: 6, confidence: 94.7, lines: 8 },
  { session: 7, confidence: 93.9, lines: 8 },
  { session: 8, confidence: 95.2, lines: 8 },
  { session: 9, confidence: 94.1, lines: 7 },
  { session: 10, confidence: 95.8, lines: 8 },
  { session: 11, confidence: 94.6, lines: 8 },
  { session: 12, confidence: 96.3, lines: 8 },
  { session: 13, confidence: 95.4, lines: 8 },
  { session: 14, confidence: 96.8, lines: 8 },
  { session: 15, confidence: 96.1, lines: 8 },
];

export const HandAiAnalyticsPage: React.FC = () => {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  // SVG dimensions for Confidence Trend line chart
  const svgW = 600;
  const svgH = 220;
  const padL = 45;
  const padR = 25;
  const padT = 20;
  const padB = 35;

  const minConf = 85;
  const maxConf = 100;

  const getX = (idx: number) => padL + (idx / (CONFIDENCE_TREND.length - 1)) * (svgW - padL - padR);
  const getY = (val: number) => padT + (1 - (val - minConf) / (maxConf - minConf)) * (svgH - padT - padB);

  const pointsPath = CONFIDENCE_TREND.map((d, i) => `${getX(i)},${getY(d.confidence)}`).join(' ');
  const areaPath = `${getX(0)},${getY(minConf)} ${pointsPath} ${getX(CONFIDENCE_TREND.length - 1)},${getY(minConf)}`;

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: '#F8FAFC' }}>
      <AdminTopbar
        title="HandAI Analytics"
        subtitle="Vietnamese Primary Student Handwriting Recognition Research Dashboard"
      />

      <Box sx={{ p: { xs: 2, md: 4 } }}>
        {/* Research Lab Header Banner */}
        <Paper
          elevation={0}
          sx={{
            p: 3,
            mb: 4,
            borderRadius: 3,
            background: 'linear-gradient(135deg, #0F172A 0%, #1E3A8A 50%, #1E40AF 100%)',
            color: '#FFFFFF',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: 2,
            border: '1px solid #1E293B',
          }}
        >
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1 }}>
              <Chip
                label="RESEARCH DASHBOARD"
                size="small"
                sx={{
                  bgcolor: 'rgba(56, 189, 248, 0.2)',
                  color: '#38BDF8',
                  border: '1px solid rgba(56, 189, 248, 0.4)',
                  fontWeight: 700,
                  fontSize: '0.7rem',
                }}
              />
              <Chip
                label="STANDALONE MODE"
                size="small"
                sx={{
                  bgcolor: 'rgba(16, 185, 129, 0.2)',
                  color: '#34D399',
                  border: '1px solid rgba(16, 185, 129, 0.4)',
                  fontWeight: 700,
                  fontSize: '0.7rem',
                }}
              />
            </Box>
            <Typography variant="h5" sx={{ fontWeight: 800, letterSpacing: '-0.02em', mb: 0.5 }}>
              HandAI Big Data Analytics
            </Typography>
            <Typography variant="body2" sx={{ color: '#94A3B8', maxWidth: 700 }}>
              Autonomous telemetry for primary student Vietnamese handwriting recognition. Isolated from
              MathVision school operations; displays real-time OCR confidence scores, advisor arbitration breakdown,
              and dataset metrics.
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 0.5 }}>
            <Typography variant="caption" sx={{ color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Target Cohort
            </Typography>
            <Chip
              label="Primary Students Grade 1-5"
              sx={{ bgcolor: '#1E293B', color: '#F8FAFC', fontWeight: 600 }}
            />
          </Box>
        </Paper>

        {/* 1. Recognition Overview Cards */}
        <Typography variant="subtitle1" sx={{ fontWeight: 700, color: '#0F172A', mb: 2 }}>
          Recognition Overview
        </Typography>
        <Grid container spacing={3} sx={{ mb: 4 }}>
          {/* Total Images Processed */}
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card elevation={0} sx={{ borderRadius: 3, border: '1px solid #E2E8F0', height: '100%' }}>
              <CardContent sx={{ p: 2.5 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1.5 }}>
                  <Typography variant="body2" sx={{ color: '#64748B', fontWeight: 600 }}>
                    Total Images Processed
                  </Typography>
                  <Box sx={{ p: 1, borderRadius: 2, bgcolor: '#EFF6FF', color: '#1D4ED8' }}>
                    <PhotoLibraryIcon fontSize="small" />
                  </Box>
                </Box>
                <Typography variant="h4" sx={{ fontWeight: 800, color: '#0F172A', mb: 0.5 }}>
                  1,280
                </Typography>
                <Typography variant="caption" sx={{ color: '#059669', fontWeight: 600 }}>
                  ↑ 100% Original Notebook Sources
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* Total Lines Recognized */}
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card elevation={0} sx={{ borderRadius: 3, border: '1px solid #E2E8F0', height: '100%' }}>
              <CardContent sx={{ p: 2.5 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1.5 }}>
                  <Typography variant="body2" sx={{ color: '#64748B', fontWeight: 600 }}>
                    Total Lines Recognized
                  </Typography>
                  <Box sx={{ p: 1, borderRadius: 2, bgcolor: '#F0FDF4', color: '#15803D' }}>
                    <FormatListNumberedIcon fontSize="small" />
                  </Box>
                </Box>
                <Typography variant="h4" sx={{ fontWeight: 800, color: '#0F172A', mb: 0.5 }}>
                  10,240
                </Typography>
                <Typography variant="caption" sx={{ color: '#64748B' }}>
                  Average 8.0 lines / page detected
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* Average Confidence Score */}
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card elevation={0} sx={{ borderRadius: 3, border: '1px solid #E2E8F0', height: '100%' }}>
              <CardContent sx={{ p: 2.5 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1.5 }}>
                  <Typography variant="body2" sx={{ color: '#64748B', fontWeight: 600 }}>
                    Average Confidence Score
                  </Typography>
                  <Box sx={{ p: 1, borderRadius: 2, bgcolor: '#EEF2FF', color: '#4F46E5' }}>
                    <TrendingUpIcon fontSize="small" />
                  </Box>
                </Box>
                <Typography variant="h4" sx={{ fontWeight: 800, color: '#0F172A', mb: 0.5 }}>
                  93.8%
                </Typography>
                <Typography variant="caption" sx={{ color: '#4F46E5', fontWeight: 600 }}>
                  CRNN + CTC Model Metric
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* AI Correction Rate */}
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card elevation={0} sx={{ borderRadius: 3, border: '1px solid #E2E8F0', height: '100%' }}>
              <CardContent sx={{ p: 2.5 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1.5 }}>
                  <Typography variant="body2" sx={{ color: '#64748B', fontWeight: 600 }}>
                    AI Correction Rate
                  </Typography>
                  <Box sx={{ p: 1, borderRadius: 2, bgcolor: '#FEF3C7', color: '#B45309' }}>
                    <AutoAwesomeIcon fontSize="small" />
                  </Box>
                </Box>
                <Typography variant="h4" sx={{ fontWeight: 800, color: '#0F172A', mb: 0.5 }}>
                  13.5%
                </Typography>
                <Typography variant="caption" sx={{ color: '#B45309' }}>
                  Tone mark & spelling arbitration
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* 2 & 3. Confidence Trend Chart & OCR Arbitration Chart */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          {/* 2. Confidence Trend Chart */}
          <Grid size={{ xs: 12, lg: 7 }}>
            <Card elevation={0} sx={{ borderRadius: 3, border: '1px solid #E2E8F0', height: '100%' }}>
              <CardContent sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Box>
                    <Typography variant="h6" sx={{ fontWeight: 700, color: '#0F172A' }}>
                      Confidence Trend Chart
                    </Typography>
                    <Typography variant="caption" sx={{ color: '#64748B' }}>
                      Session number vs. Recognition Confidence Score (last 15 sessions)
                    </Typography>
                  </Box>
                  <Chip
                    label="Metric: Confidence Score"
                    size="small"
                    sx={{ bgcolor: '#EFF6FF', color: '#1D4ED8', fontWeight: 600, fontSize: '0.75rem' }}
                  />
                </Box>

                {/* Responsive SVG Line Chart */}
                <Box sx={{ width: '100%', overflowX: 'auto', display: 'flex', justifyContent: 'center' }}>
                  <svg
                    viewBox={`0 0 ${svgW} ${svgH}`}
                    style={{ width: '100%', maxWidth: svgW, height: 'auto', display: 'block' }}
                  >
                    <defs>
                      <linearGradient id="trendGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#1E40AF" stopOpacity="0.25" />
                        <stop offset="100%" stopColor="#1E40AF" stopOpacity="0.0" />
                      </linearGradient>
                    </defs>

                    {/* Horizontal Grid lines */}
                    {[85, 90, 95, 100].map((v) => (
                      <g key={v}>
                        <line
                          x1={padL}
                          y1={getY(v)}
                          x2={svgW - padR}
                          y2={getY(v)}
                          stroke="#E2E8F0"
                          strokeDasharray="4 4"
                          strokeWidth="1"
                        />
                        <text
                          x={padL - 8}
                          y={getY(v) + 4}
                          textAnchor="end"
                          fontSize="10"
                          fill="#94A3B8"
                          fontWeight="500"
                        >
                          {v}%
                        </text>
                      </g>
                    ))}

                    {/* Gradient Area Fill */}
                    <polygon points={areaPath} fill="url(#trendGradient)" />

                    {/* Line Chart Path */}
                    <polyline
                      fill="none"
                      stroke="#1E40AF"
                      strokeWidth="2.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      points={pointsPath}
                    />

                    {/* Data Points */}
                    {CONFIDENCE_TREND.map((d, i) => {
                      const cx = getX(i);
                      const cy = getY(d.confidence);
                      const isHovered = hoveredIndex === i;
                      return (
                        <g
                          key={d.session}
                          onMouseEnter={() => setHoveredIndex(i)}
                          onMouseLeave={() => setHoveredIndex(null)}
                          style={{ cursor: 'pointer' }}
                        >
                          <circle
                            cx={cx}
                            cy={cy}
                            r={isHovered ? 6 : 4}
                            fill="#FFFFFF"
                            stroke="#1E40AF"
                            strokeWidth={isHovered ? 3 : 2}
                          />
                          {/* X-axis session labels */}
                          {(i === 0 || i === 4 || i === 9 || i === 14) && (
                            <text
                              x={cx}
                              y={svgH - 12}
                              textAnchor="middle"
                              fontSize="10"
                              fill="#64748B"
                              fontWeight="600"
                            >
                              S{d.session}
                            </text>
                          )}
                          {isHovered && (
                            <g>
                              <rect
                                x={cx - 38}
                                y={cy - 28}
                                width="76"
                                height="22"
                                rx="4"
                                fill="#0F172A"
                              />
                              <text
                                x={cx}
                                y={cy - 14}
                                textAnchor="middle"
                                fontSize="11"
                                fill="#FFFFFF"
                                fontWeight="700"
                              >
                                {d.confidence}% conf
                              </text>
                            </g>
                          )}
                        </g>
                      );
                    })}
                  </svg>
                </Box>
                <Typography variant="caption" sx={{ color: '#94A3B8', display: 'block', textAlign: 'center', mt: 1 }}>
                  X-Axis: Research Session Index • Y-Axis: Model Confidence Score
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* 3. OCR Arbitration Chart */}
          <Grid size={{ xs: 12, lg: 5 }}>
            <Card elevation={0} sx={{ borderRadius: 3, border: '1px solid #E2E8F0', height: '100%' }}>
              <CardContent sx={{ p: 3 }}>
                <Typography variant="h6" sx={{ fontWeight: 700, color: '#0F172A', mb: 0.5 }}>
                  OCR Arbitration Chart
                </Typography>
                <Typography variant="caption" sx={{ color: '#64748B', display: 'block', mb: 3 }}>
                  Distribution of final line texts accepted by source provenance
                </Typography>

                {/* Segmented Bar Visualization */}
                <Box sx={{ display: 'flex', height: 18, borderRadius: 2, overflow: 'hidden', mb: 3 }}>
                  <Box sx={{ width: '82.1%', bgcolor: '#3B82F6' }} title="Raw OCR Accepted (82.1%)" />
                  <Box sx={{ width: '13.5%', bgcolor: '#F59E0B' }} title="AI Correction Applied (13.5%)" />
                  <Box sx={{ width: '4.4%', bgcolor: '#10B981' }} title="Manual Edit (4.4%)" />
                </Box>

                {/* Breakdown Details List */}
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  {/* Raw OCR Accepted */}
                  <Box sx={{ p: 1.5, borderRadius: 2, bgcolor: '#F1F5F9', border: '1px solid #CBD5E1' }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Box sx={{ width: 10, height: 10, borderRadius: '50%', bgcolor: '#3B82F6' }} />
                        <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#334155' }}>
                          Raw OCR Accepted
                        </Typography>
                      </Box>
                      <Typography variant="subtitle2" sx={{ fontWeight: 800, color: '#1E40AF' }}>
                        82.1% (8,407 lines)
                      </Typography>
                    </Box>
                    <Typography variant="caption" sx={{ color: '#64748B' }}>
                      Baseline CRNN sequence prediction accepted without modification.
                    </Typography>
                  </Box>

                  {/* AI Correction Applied */}
                  <Box sx={{ p: 1.5, borderRadius: 2, bgcolor: '#FEF3C7', border: '1px solid #FCD34D' }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Box sx={{ width: 10, height: 10, borderRadius: '50%', bgcolor: '#F59E0B' }} />
                        <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#78350F' }}>
                          AI Correction Applied
                        </Typography>
                      </Box>
                      <Typography variant="subtitle2" sx={{ fontWeight: 800, color: '#B45309' }}>
                        13.5% (1,382 lines)
                      </Typography>
                    </Box>
                    <Typography variant="caption" sx={{ color: '#92400E' }}>
                      Advisor suggestions selected due to invalid spelling or tone patterns.
                    </Typography>
                  </Box>

                  {/* Manual Edit */}
                  <Box sx={{ p: 1.5, borderRadius: 2, bgcolor: '#DCFCE7', border: '1px solid #86EFAC' }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Box sx={{ width: 10, height: 10, borderRadius: '50%', bgcolor: '#10B981' }} />
                        <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#166534' }}>
                          Manual Edit
                        </Typography>
                      </Box>
                      <Typography variant="subtitle2" sx={{ fontWeight: 800, color: '#15803D' }}>
                        4.4% (451 lines)
                      </Typography>
                    </Box>
                    <Typography variant="caption" sx={{ color: '#166534' }}>
                      Human operator intervention for heavily faded or distorted writing.
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* 4 & 5. Recognition Quality & Dataset Statistics */}
        <Grid container spacing={3}>
          {/* 4. Recognition Quality Distribution */}
          <Grid size={{ xs: 12, md: 6 }}>
            <Card elevation={0} sx={{ borderRadius: 3, border: '1px solid #E2E8F0', height: '100%' }}>
              <CardContent sx={{ p: 3 }}>
                <Typography variant="h6" sx={{ fontWeight: 700, color: '#0F172A', mb: 0.5 }}>
                  Recognition Quality
                </Typography>
                <Typography variant="caption" sx={{ color: '#64748B', display: 'block', mb: 3 }}>
                  Line confidence score distribution across all processed handwriting samples
                </Typography>

                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
                  {/* High Confidence */}
                  <Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="body2" sx={{ fontWeight: 600, color: '#0F172A' }}>
                        High Confidence Score (≥ 90%)
                      </Typography>
                      <Typography variant="body2" sx={{ fontWeight: 700, color: '#059669' }}>
                        85.4% (8,745 lines)
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={85.4}
                      sx={{ height: 8, borderRadius: 2, bgcolor: '#E2E8F0', '& .MuiLinearProgress-bar': { bgcolor: '#10B981' } }}
                    />
                  </Box>

                  {/* Moderate Confidence */}
                  <Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="body2" sx={{ fontWeight: 600, color: '#0F172A' }}>
                        Moderate Confidence Score (75% - 89%)
                      </Typography>
                      <Typography variant="body2" sx={{ fontWeight: 700, color: '#D97706' }}>
                        11.8% (1,208 lines)
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={11.8}
                      sx={{ height: 8, borderRadius: 2, bgcolor: '#E2E8F0', '& .MuiLinearProgress-bar': { bgcolor: '#F59E0B' } }}
                    />
                  </Box>

                  {/* Review Recommended */}
                  <Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="body2" sx={{ fontWeight: 600, color: '#0F172A' }}>
                        Review Recommended (&lt; 75%)
                      </Typography>
                      <Typography variant="body2" sx={{ fontWeight: 700, color: '#DC2626' }}>
                        2.8% (287 lines)
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={2.8}
                      sx={{ height: 8, borderRadius: 2, bgcolor: '#E2E8F0', '& .MuiLinearProgress-bar': { bgcolor: '#EF4444' } }}
                    />
                  </Box>

                  <Divider sx={{ my: 1 }} />

                  {/* Additional Telemetry Parameters */}
                  <Box sx={{ display: 'flex', justifyContent: 'space-around', textAlign: 'center', pt: 0.5 }}>
                    <Box>
                      <Typography variant="caption" sx={{ color: '#64748B', display: 'block' }}>
                        AI Agreement Rate
                      </Typography>
                      <Typography variant="subtitle1" sx={{ fontWeight: 800, color: '#0F172A' }}>
                        89.2%
                      </Typography>
                    </Box>
                    <Box>
                      <Typography variant="caption" sx={{ color: '#64748B', display: 'block' }}>
                        Mean Token Entropy
                      </Typography>
                      <Typography variant="subtitle1" sx={{ fontWeight: 800, color: '#0F172A' }}>
                        0.142
                      </Typography>
                    </Box>
                    <Box>
                      <Typography variant="caption" sx={{ color: '#64748B', display: 'block' }}>
                        CTC Blank Ratio
                      </Typography>
                      <Typography variant="subtitle1" sx={{ fontWeight: 800, color: '#0F172A' }}>
                        0.180
                      </Typography>
                    </Box>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* 5. Dataset Statistics & Research Scope */}
          <Grid size={{ xs: 12, md: 6 }}>
            <Card elevation={0} sx={{ borderRadius: 3, border: '1px solid #E2E8F0', height: '100%' }}>
              <CardContent sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                  <StorageIcon sx={{ color: '#1E40AF' }} />
                  <Typography variant="h6" sx={{ fontWeight: 700, color: '#0F172A' }}>
                    Dataset Statistics
                  </Typography>
                </Box>
                <Typography variant="caption" sx={{ color: '#64748B', display: 'block', mb: 2 }}>
                  Metadata regarding training corpus and linguistic scope
                </Typography>

                <TableContainer component={Box}>
                  <Table size="small">
                    <TableBody>
                      <TableRow>
                        <TableCell sx={{ fontWeight: 700, color: '#64748B', width: '38%' }}>Dataset Size</TableCell>
                        <TableCell sx={{ fontWeight: 600, color: '#0F172A' }}>
                          25,000+ labeled handwriting lines
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell sx={{ fontWeight: 700, color: '#64748B' }}>Language</TableCell>
                        <TableCell sx={{ fontWeight: 600, color: '#0F172A' }}>
                          Vietnamese (Unicode NFC, full diacritics & tone marks)
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell sx={{ fontWeight: 700, color: '#64748B' }}>Target Cohort</TableCell>
                        <TableCell>
                          <Chip
                            label="Primary Students Grade 1-5"
                            size="small"
                            sx={{ bgcolor: '#EFF6FF', color: '#1D4ED8', fontWeight: 700 }}
                          />
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell sx={{ fontWeight: 700, color: '#64748B' }}>Architecture</TableCell>
                        <TableCell sx={{ fontWeight: 600, color: '#0F172A' }}>
                          CRNN + CTC Greedy Decoder
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell sx={{ fontWeight: 700, color: '#64748B' }}>Segmentation</TableCell>
                        <TableCell sx={{ fontWeight: 600, color: '#0F172A' }}>
                          OpenCV Adaptive Horizontal Projection Profiling
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell sx={{ fontWeight: 700, color: '#64748B' }}>Spelling Advisor</TableCell>
                        <TableCell sx={{ fontWeight: 600, color: '#0F172A' }}>
                          Multi-Provider Consensus (Groq Llama 3 / Gemini Pro)
                        </TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>
    </Box>
  );
};
