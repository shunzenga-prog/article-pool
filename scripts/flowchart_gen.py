#!/usr/bin/env python3
"""
Flowchart generator — Design-grade Mermaid.js charts rendered via Playwright.

A complete design system for WeChat tutorial flowcharts. Every visual decision
is governed by design tokens organized into content-aware palettes. Node categories
auto-generate per-node `style` directives; edges get linkStyle directives.

NOTE: We use per-node `style` instead of `classDef` because Mermaid v11.12+
has a parser regression that breaks classDef with syntax errors.

Usage:
  python flowchart_gen.py --file flow.json -o chart.png
  python flowchart_gen.py --file flow.json -o chart.png --palette ocean --width 670
  python flowchart_gen.py --inline '{...}' --markup-only   # debug

Input JSON schema:
  {
    "direction": "LR|TB|RL|BT",
    "title": "Diagram Title",
    "palette": "tech-dark|ocean|forest|sunset|midnight|paper",
    "subgraphs": [{"title":"Zone A","nodes":["a","b"]}],
    "nodes": [
      {"id":"a", "label":"Step 1", "desc":"Description",
       "shape":"rounded|rectangle|stadium|diamond|hexagon|cylinder|subroutine|circle",
       "category":"step|start|end|decision|data|highlight|external",
       "icon":"📦"}
    ],
    "edges": [
      {"from":"a","to":"b","label":"→","category":"main|data|feedback|trigger"}
    ]
  }

Node categories → automatic classDef styling:
  step       — process step (primary fill, rounded)
  start/end  — terminal (subtle fill, stadium)
  decision   — branch (accent fill, diamond)
  data       — storage (neutral fill, cylinder)
  highlight  — key step (bold fill, subroutine)
  external   — outside system (muted fill, hexagon)

Edge categories → automatic linkStyle:
  main       — solid thick arrow (primary color)
  data       — solid thin arrow (tertiary color)
  feedback   — dashed arrow (warm color)
  trigger    — dotted arrow (muted color)
"""

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

# ═══════════════════════════════════════════════════════════════
# Design Token System — Complete palettes with category-level tokens
# ═══════════════════════════════════════════════════════════════

PALETTES = {
    # ── Tech Dark: AI / coding tutorials (default) ──
    "tech-dark": {
        "meta": {"name": "科技暗色", "mood": "专业、冷静、未来感"},
        "canvas": "#0a0d18",
        "surface": "#1c1d2e",
        "text": "#c8cde0",
        "text_dim": "#7c8099",
        "line": "#404360",
        "line_strong": "#5b6099",
        "categories": {
            "step":    {"fill": "#252740", "border": "#5865f2", "text": "#d4d8f0"},
            "start":   {"fill": "#1e2a24", "border": "#3ba55c", "text": "#b8d4c0"},
            "end":     {"fill": "#2a1e24", "border": "#ed4245", "text": "#d4b8bc"},
            "decision":{"fill": "#2a241e", "border": "#f0a020", "text": "#d4c8b0"},
            "data":    {"fill": "#1e242a", "border": "#4a90d9", "text": "#b0c4d4"},
            "highlight":{"fill":"#25223a", "border": "#9b59b6", "text": "#d0b8e0"},
            "external":{"fill": "#232328", "border": "#5c5e6e", "text": "#b0b0c0"},
        },
        "subgraph": {"fill": "#161722", "border": "#303245", "text": "#7c8099"},
        "edges": {
            "main":     {"color": "#5865f2", "width": 2.5},
            "data":     {"color": "#4a90d9", "width": 1.5},
            "feedback": {"color": "#f0a020", "width": 1.5, "dash": "4,4"},
            "trigger":  {"color": "#5c5e6e", "width": 1.0, "dash": "2,4"},
        },
        "font": {"family": "system-ui, sans-serif", "size": 14},
        "effects": {
            "canvas_glow_top": "rgba(59,130,246,0.06)",
            "canvas_glow_bottom": "rgba(139,92,246,0.04)",
            "card_bg_start": "rgba(22,25,42,0.88)",
            "card_bg_end": "rgba(28,31,52,0.88)",
            "card_border": "rgba(99,102,241,0.12)",
            "card_highlight": "rgba(255,255,255,0.03)",
            "accent_from": "#3b82f6",
            "accent_to": "#8b5cf6",
            "edge_gradient_from": "#5865f2",
            "edge_gradient_to": "#a78bfa",
            "gradient_boost": 0.18,
        },
    },

    # ── Ocean: system architecture / infrastructure ──
    "ocean": {
        "meta": {"name": "深海蓝", "mood": "稳重、深邃、架构感"},
        "canvas": "#0a1628",
        "surface": "#0f2035",
        "text": "#b8d0e8",
        "text_dim": "#5a7a9a",
        "line": "#1e3a58",
        "line_strong": "#2a6090",
        "categories": {
            "step":    {"fill": "#0d2540", "border": "#3498db", "text": "#c0daf0"},
            "start":   {"fill": "#0d2818", "border": "#27ae60", "text": "#a0d8b8"},
            "end":     {"fill": "#28101a", "border": "#e74c3c", "text": "#d8a8b0"},
            "decision":{"fill": "#281a08", "border": "#f39c12", "text": "#d8c8a0"},
            "data":    {"fill": "#0d1a28", "border": "#2980b9", "text": "#a0c0d8"},
            "highlight":{"fill":"#1a1030", "border": "#8e44ad", "text": "#c8b0e0"},
            "external":{"fill": "#121a22", "border": "#405060", "text": "#90a0b0"},
        },
        "subgraph": {"fill": "#081420", "border": "#1a3050", "text": "#4a6a8a"},
        "edges": {
            "main":     {"color": "#3498db", "width": 2.5},
            "data":     {"color": "#2980b9", "width": 1.5},
            "feedback": {"color": "#f39c12", "width": 1.5, "dash": "4,4"},
            "trigger":  {"color": "#405060", "width": 1.0, "dash": "2,4"},
        },
        "font": {"family": "system-ui, sans-serif", "size": 14},
        "effects": {
            "canvas_glow_top": "rgba(52,152,219,0.06)",
            "canvas_glow_bottom": "rgba(41,128,185,0.04)",
            "card_bg_start": "rgba(10,20,35,0.88)",
            "card_bg_end": "rgba(15,28,48,0.88)",
            "card_border": "rgba(52,152,219,0.10)",
            "card_highlight": "rgba(255,255,255,0.02)",
            "accent_from": "#3498db",
            "accent_to": "#2980b9",
            "edge_gradient_from": "#3498db",
            "edge_gradient_to": "#5dade2",
            "gradient_boost": 0.15,
        },
    },

    # ── Forest: nature / energy / sustainability ──
    "forest": {
        "meta": {"name": "森林绿", "mood": "自然、生长、可持续"},
        "canvas": "#0d1a12",
        "surface": "#14281e",
        "text": "#b0d0b8",
        "text_dim": "#4a7a5a",
        "line": "#1a4028",
        "line_strong": "#2a7040",
        "categories": {
            "step":    {"fill": "#0f2818", "border": "#2ecc71", "text": "#b8e8c8"},
            "start":   {"fill": "#0f2018", "border": "#1abc9c", "text": "#a0d8c0"},
            "end":     {"fill": "#20101a", "border": "#e67e22", "text": "#d8b8a0"},
            "decision":{"fill": "#1a1808", "border": "#f1c40f", "text": "#c8c0a0"},
            "data":    {"fill": "#0d1a18", "border": "#16a085", "text": "#a0c8b8"},
            "highlight":{"fill":"#181030", "border": "#9b59b6", "text": "#c8b0e0"},
            "external":{"fill": "#121a16", "border": "#3a5040", "text": "#90a898"},
        },
        "subgraph": {"fill": "#08140c", "border": "#1a4028", "text": "#3a6a4a"},
        "edges": {
            "main":     {"color": "#2ecc71", "width": 2.5},
            "data":     {"color": "#16a085", "width": 1.5},
            "feedback": {"color": "#e67e22", "width": 1.5, "dash": "4,4"},
            "trigger":  {"color": "#3a5040", "width": 1.0, "dash": "2,4"},
        },
        "font": {"family": "system-ui, sans-serif", "size": 14},
        "effects": {
            "canvas_glow_top": "rgba(46,204,113,0.05)",
            "canvas_glow_bottom": "rgba(26,188,156,0.03)",
            "card_bg_start": "rgba(8,22,14,0.88)",
            "card_bg_end": "rgba(14,32,24,0.88)",
            "card_border": "rgba(46,204,113,0.10)",
            "card_highlight": "rgba(255,255,255,0.02)",
            "accent_from": "#2ecc71",
            "accent_to": "#1abc9c",
            "edge_gradient_from": "#2ecc71",
            "edge_gradient_to": "#58d68d",
            "gradient_boost": 0.15,
        },
    },

    # ── Sunset: creative / opinion / lifestyle ──
    "sunset": {
        "meta": {"name": "日落暖", "mood": "温暖、创造、人文感"},
        "canvas": "#1a1410",
        "surface": "#281c18",
        "text": "#d8c8b8",
        "text_dim": "#8a7060",
        "line": "#403020",
        "line_strong": "#705030",
        "categories": {
            "step":    {"fill": "#281808", "border": "#e67e22", "text": "#e8d0b8"},
            "start":   {"fill": "#181808", "border": "#f1c40f", "text": "#d8d0a0"},
            "end":     {"fill": "#20101a", "border": "#e74c3c", "text": "#d8b0b0"},
            "decision":{"fill": "#201800", "border": "#f39c12", "text": "#d8c8a0"},
            "data":    {"fill": "#181410", "border": "#d35400", "text": "#c8b098"},
            "highlight":{"fill":"#201030", "border": "#c0392b", "text": "#e0b8b8"},
            "external":{"fill": "#161210", "border": "#4a3a2a", "text": "#a09080"},
        },
        "subgraph": {"fill": "#0e0a08", "border": "#302018", "text": "#6a5040"},
        "edges": {
            "main":     {"color": "#e67e22", "width": 2.5},
            "data":     {"color": "#d35400", "width": 1.5},
            "feedback": {"color": "#f1c40f", "width": 1.5, "dash": "4,4"},
            "trigger":  {"color": "#4a3a2a", "width": 1.0, "dash": "2,4"},
        },
        "font": {"family": "system-ui, sans-serif", "size": 14},
        "effects": {
            "canvas_glow_top": "rgba(230,126,34,0.05)",
            "canvas_glow_bottom": "rgba(241,196,15,0.03)",
            "card_bg_start": "rgba(26,18,14,0.88)",
            "card_bg_end": "rgba(35,24,20,0.88)",
            "card_border": "rgba(230,126,34,0.10)",
            "card_highlight": "rgba(255,255,255,0.02)",
            "accent_from": "#e67e22",
            "accent_to": "#f1c40f",
            "edge_gradient_from": "#e67e22",
            "edge_gradient_to": "#f39c12",
            "gradient_boost": 0.15,
        },
    },

    # ── Midnight: startup / innovation / VC ──
    "midnight": {
        "meta": {"name": "极夜黑", "mood": "现代、锐利、极客感"},
        "canvas": "#08080c",
        "surface": "#101018",
        "text": "#c0c0d0",
        "text_dim": "#585870",
        "line": "#282840",
        "line_strong": "#4848a0",
        "categories": {
            "step":    {"fill": "#14142a", "border": "#7c3aed", "text": "#d0c8f8"},
            "start":   {"fill": "#0a1a14", "border": "#10b981", "text": "#a0e0c0"},
            "end":     {"fill": "#1a0a14", "border": "#f43f5e", "text": "#e0b0c0"},
            "decision":{"fill": "#1a1408", "border": "#f59e0b", "text": "#e0d0a0"},
            "data":    {"fill": "#0a1420", "border": "#3b82f6", "text": "#b0c8e8"},
            "highlight":{"fill":"#1a1030", "border": "#ec4899", "text": "#e8c0d8"},
            "external":{"fill": "#101018", "border": "#404050", "text": "#9090a0"},
        },
        "subgraph": {"fill": "#04040a", "border": "#202038", "text": "#484868"},
        "edges": {
            "main":     {"color": "#7c3aed", "width": 2.5},
            "data":     {"color": "#3b82f6", "width": 1.5},
            "feedback": {"color": "#f59e0b", "width": 1.5, "dash": "4,4"},
            "trigger":  {"color": "#404050", "width": 1.0, "dash": "2,4"},
        },
        "font": {"family": "system-ui, sans-serif", "size": 14},
        "effects": {
            "canvas_glow_top": "rgba(124,58,237,0.06)",
            "canvas_glow_bottom": "rgba(236,72,153,0.04)",
            "card_bg_start": "rgba(10,10,18,0.88)",
            "card_bg_end": "rgba(16,16,28,0.88)",
            "card_border": "rgba(124,58,237,0.12)",
            "card_highlight": "rgba(255,255,255,0.02)",
            "accent_from": "#7c3aed",
            "accent_to": "#ec4899",
            "edge_gradient_from": "#7c3aed",
            "edge_gradient_to": "#a78bfa",
            "gradient_boost": 0.18,
        },
    },

    # ── Paper: literature / history / education ──
    "paper": {
        "meta": {"name": "宣纸白", "mood": "优雅、人文、书卷气"},
        "canvas": "#faf8f2",
        "surface": "#f4f0e8",
        "text": "#2c2820",
        "text_dim": "#8c8070",
        "line": "#d8d0c0",
        "line_strong": "#b0a090",
        "categories": {
            "step":    {"fill": "#f0ece4", "border": "#4a6741", "text": "#2c3028"},
            "start":   {"fill": "#eef4ec", "border": "#6b8c5c", "text": "#283020"},
            "end":     {"fill": "#f4ecee", "border": "#8b5c4a", "text": "#302420"},
            "decision":{"fill": "#f4f0e4", "border": "#8c7a30", "text": "#302c20"},
            "data":    {"fill": "#ecf0f4", "border": "#4a668b", "text": "#202830"},
            "highlight":{"fill":"#f0e8f4", "border": "#7a4a8b", "text": "#2c2030"},
            "external":{"fill": "#f4f2ee", "border": "#b0a898", "text": "#504840"},
        },
        "subgraph": {"fill": "#f8f6f0", "border": "#d0c8b8", "text": "#8c8070"},
        "edges": {
            "main":     {"color": "#4a6741", "width": 2.5},
            "data":     {"color": "#4a668b", "width": 1.5},
            "feedback": {"color": "#8c7a30", "width": 1.5, "dash": "4,4"},
            "trigger":  {"color": "#b0a898", "width": 1.0, "dash": "2,4"},
        },
        "font": {"family": "system-ui, sans-serif", "size": 14},
        "effects": {
            "canvas_glow_top": "rgba(74,103,65,0.04)",
            "canvas_glow_bottom": "rgba(107,140,92,0.03)",
            "card_bg_start": "rgba(255,252,244,0.90)",
            "card_bg_end": "rgba(248,244,232,0.90)",
            "card_border": "rgba(180,160,140,0.25)",
            "card_highlight": "rgba(255,255,255,0.6)",
            "accent_from": "#4a6741",
            "accent_to": "#6b8c5c",
            "edge_gradient_from": "#4a6741",
            "edge_gradient_to": "#6b8c5c",
            "gradient_boost": -0.08,
        },
    },

    # ── Cyberpunk: neon cyan/magenta on deep dark, for gaming / creative tech ──
    "cyberpunk": {
        "meta": {"name": "赛博朋克", "mood": "霓虹、反叛、未来感"},
        "canvas": "#050510",
        "surface": "#0e0e1a",
        "text": "#c8e8ff",
        "text_dim": "#5a8099",
        "line": "#1a2040",
        "line_strong": "#2a5090",
        "categories": {
            "step":    {"fill": "#0d1a28", "border": "#00f0ff", "text": "#b8f0ff"},
            "start":   {"fill": "#0d1a10", "border": "#00ff88", "text": "#b0ffc8"},
            "end":     {"fill": "#1a0d20", "border": "#ff00aa", "text": "#f0b8d8"},
            "decision":{"fill": "#1a1808", "border": "#ffe600", "text": "#f0e8b0"},
            "data":    {"fill": "#0a1628", "border": "#4488ff", "text": "#b0c8f0"},
            "highlight":{"fill":"#180d28", "border": "#cc44ff", "text": "#d8b8f0"},
            "external":{"fill": "#0e0e18", "border": "#304060", "text": "#8090b0"},
        },
        "subgraph": {"fill": "#06060e", "border": "#1a3050", "text": "#4a6090"},
        "edges": {
            "main":     {"color": "#00f0ff", "width": 2.5},
            "data":     {"color": "#4488ff", "width": 1.5},
            "feedback": {"color": "#ff00aa", "width": 1.5, "dash": "4,4"},
            "trigger":  {"color": "#ffe600", "width": 1.0, "dash": "2,4"},
        },
        "font": {"family": "system-ui, sans-serif", "size": 14},
        "effects": {
            "canvas_glow_top": "rgba(0,240,255,0.10)",
            "canvas_glow_bottom": "rgba(255,0,170,0.06)",
            "card_bg_start": "rgba(8,8,20,0.90)",
            "card_bg_end": "rgba(14,14,26,0.90)",
            "card_border": "rgba(0,240,255,0.15)",
            "card_border_glow": "rgba(0,240,255,0.25)",
            "card_highlight": "rgba(0,240,255,0.04)",
            "glow_ring": "rgba(0,240,255,0.08)",
            "accent_from": "#00f0ff",
            "accent_to": "#ff00aa",
            "edge_gradient_from": "#00f0ff",
            "edge_gradient_to": "#ff00aa",
            "gradient_boost": 0.25,
        },
    },

    # ── Ember: warm amber/orange on dark, for opinion / hot takes ──
    "ember": {
        "meta": {"name": "炭火余烬", "mood": "炽热、态度、情感"},
        "canvas": "#1a0e08",
        "surface": "#241610",
        "text": "#e8d0b8",
        "text_dim": "#8a6050",
        "line": "#3a2018",
        "line_strong": "#6a3828",
        "categories": {
            "step":    {"fill": "#2a1808", "border": "#f59e0b", "text": "#f0d8b0"},
            "start":   {"fill": "#1a2408", "border": "#84cc16", "text": "#c8e0a0"},
            "end":     {"fill": "#240a10", "border": "#ef4444", "text": "#e8b0b0"},
            "decision":{"fill": "#241808", "border": "#ea580c", "text": "#e8c898"},
            "data":    {"fill": "#1a1008", "border": "#d97706", "text": "#d8b890"},
            "highlight":{"fill":"#240818", "border": "#f97316", "text": "#e8b8a0"},
            "external":{"fill": "#181008", "border": "#4a3020", "text": "#a08070"},
        },
        "subgraph": {"fill": "#0e0804", "border": "#2a1810", "text": "#6a4030"},
        "edges": {
            "main":     {"color": "#f59e0b", "width": 2.5},
            "data":     {"color": "#d97706", "width": 1.5},
            "feedback": {"color": "#ef4444", "width": 1.5, "dash": "4,4"},
            "trigger":  {"color": "#ea580c", "width": 1.0, "dash": "2,4"},
        },
        "font": {"family": "system-ui, sans-serif", "size": 14},
        "effects": {
            "canvas_glow_top": "rgba(245,158,11,0.08)",
            "canvas_glow_bottom": "rgba(239,68,68,0.04)",
            "card_bg_start": "rgba(26,14,6,0.88)",
            "card_bg_end": "rgba(32,20,14,0.88)",
            "card_border": "rgba(245,158,11,0.12)",
            "card_border_glow": "rgba(245,158,11,0.22)",
            "card_highlight": "rgba(255,255,255,0.03)",
            "glow_ring": "rgba(245,158,11,0.06)",
            "accent_from": "#f59e0b",
            "accent_to": "#ef4444",
            "edge_gradient_from": "#f59e0b",
            "edge_gradient_to": "#ea580c",
            "gradient_boost": 0.18,
        },
    },

    # ── Aurora: teal/cyan/violet northern lights, for nature / science ──
    "aurora": {
        "meta": {"name": "极光幻境", "mood": "通透、自然、科技感"},
        "canvas": "#0a1628",
        "surface": "#0e2038",
        "text": "#b8e0e8",
        "text_dim": "#4a8090",
        "line": "#1a3850",
        "line_strong": "#2a6890",
        "categories": {
            "step":    {"fill": "#0a2828", "border": "#14b8a6", "text": "#b0f0e0"},
            "start":   {"fill": "#0a2818", "border": "#10b981", "text": "#a0e8b8"},
            "end":     {"fill": "#200a28", "border": "#8b5cf6", "text": "#c8b0e8"},
            "decision":{"fill": "#182008", "border": "#22d3ee", "text": "#b8e8d0"},
            "data":    {"fill": "#0a1828", "border": "#06b6d4", "text": "#a0d0e0"},
            "highlight":{"fill":"#180a28", "border": "#a78bfa", "text": "#d0b8f0"},
            "external":{"fill": "#0e1820", "border": "#305060", "text": "#80a0b0"},
        },
        "subgraph": {"fill": "#060e18", "border": "#1a3850", "text": "#3a6880"},
        "edges": {
            "main":     {"color": "#14b8a6", "width": 2.5},
            "data":     {"color": "#06b6d4", "width": 1.5},
            "feedback": {"color": "#8b5cf6", "width": 1.5, "dash": "4,4"},
            "trigger":  {"color": "#22d3ee", "width": 1.0, "dash": "2,4"},
        },
        "font": {"family": "system-ui, sans-serif", "size": 14},
        "effects": {
            "canvas_glow_top": "rgba(20,184,166,0.06)",
            "canvas_glow_bottom": "rgba(139,92,246,0.05)",
            "card_bg_start": "rgba(8,18,32,0.88)",
            "card_bg_end": "rgba(14,26,46,0.88)",
            "card_border": "rgba(20,184,166,0.12)",
            "card_border_glow": "rgba(20,184,166,0.22)",
            "card_highlight": "rgba(255,255,255,0.03)",
            "glow_ring": "rgba(20,184,166,0.06)",
            "accent_from": "#14b8a6",
            "accent_to": "#8b5cf6",
            "edge_gradient_from": "#14b8a6",
            "edge_gradient_to": "#06b6d4",
            "gradient_boost": 0.18,
        },
    },

    # ── Navy: navy blue + gold, for business / finance / enterprise ──
    "navy": {
        "meta": {"name": "海军蓝金", "mood": "权威、信赖、高端"},
        "canvas": "#0c1628",
        "surface": "#14203a",
        "text": "#c8d8f0",
        "text_dim": "#5a7099",
        "line": "#1a3060",
        "line_strong": "#2a50a0",
        "categories": {
            "step":    {"fill": "#101e38", "border": "#38bdf8", "text": "#c0ddf8"},
            "start":   {"fill": "#102018", "border": "#22c55e", "text": "#a8d8b8"},
            "end":     {"fill": "#201020", "border": "#f87171", "text": "#e0b8b8"},
            "decision":{"fill": "#1a1808", "border": "#eab308", "text": "#e0d090"},
            "data":    {"fill": "#0e1828", "border": "#60a5fa", "text": "#b0c8e8"},
            "highlight":{"fill":"#181030", "border": "#a78bfa", "text": "#d0b8f0"},
            "external":{"fill": "#101420", "border": "#304870", "text": "#8098b8"},
        },
        "subgraph": {"fill": "#080e18", "border": "#1a3060", "text": "#4a6090"},
        "edges": {
            "main":     {"color": "#38bdf8", "width": 2.5},
            "data":     {"color": "#60a5fa", "width": 1.5},
            "feedback": {"color": "#eab308", "width": 1.5, "dash": "4,4"},
            "trigger":  {"color": "#f87171", "width": 1.0, "dash": "2,4"},
        },
        "font": {"family": "system-ui, sans-serif", "size": 14},
        "effects": {
            "canvas_glow_top": "rgba(56,189,248,0.06)",
            "canvas_glow_bottom": "rgba(234,179,8,0.04)",
            "card_bg_start": "rgba(10,18,34,0.88)",
            "card_bg_end": "rgba(16,26,50,0.88)",
            "card_border": "rgba(56,189,248,0.10)",
            "card_border_glow": "rgba(56,189,248,0.20)",
            "card_highlight": "rgba(255,255,255,0.03)",
            "glow_ring": "rgba(56,189,248,0.06)",
            "accent_from": "#38bdf8",
            "accent_to": "#eab308",
            "edge_gradient_from": "#38bdf8",
            "edge_gradient_to": "#60a5fa",
            "gradient_boost": 0.16,
        },
    },

    # ── Slate: cool gray/blue-gray professional, for analysis / research ──
    "slate": {
        "meta": {"name": "岩板灰", "mood": "理性、冷静、专业"},
        "canvas": "#1a1f2e",
        "surface": "#242a3a",
        "text": "#c8cdd8",
        "text_dim": "#6a7088",
        "line": "#303650",
        "line_strong": "#485878",
        "categories": {
            "step":    {"fill": "#262c40", "border": "#94a3b8", "text": "#d0d4e0"},
            "start":   {"fill": "#1e2824", "border": "#86a898", "text": "#b8c8c0"},
            "end":     {"fill": "#281e24", "border": "#b89090", "text": "#d0b8b8"},
            "decision":{"fill": "#28281c", "border": "#a89860", "text": "#d0c8a8"},
            "data":    {"fill": "#1e242c", "border": "#7088a8", "text": "#b0bcc8"},
            "highlight":{"fill":"#24203a", "border": "#9890c8", "text": "#c8c0e0"},
            "external":{"fill": "#1e2030", "border": "#485060", "text": "#8890a0"},
        },
        "subgraph": {"fill": "#121620", "border": "#2a3048", "text": "#586080"},
        "edges": {
            "main":     {"color": "#94a3b8", "width": 2.5},
            "data":     {"color": "#7088a8", "width": 1.5},
            "feedback": {"color": "#a89860", "width": 1.5, "dash": "4,4"},
            "trigger":  {"color": "#485060", "width": 1.0, "dash": "2,4"},
        },
        "font": {"family": "system-ui, sans-serif", "size": 14},
        "effects": {
            "canvas_glow_top": "rgba(148,163,184,0.04)",
            "canvas_glow_bottom": "rgba(112,136,168,0.03)",
            "card_bg_start": "rgba(24,30,42,0.90)",
            "card_bg_end": "rgba(32,38,52,0.90)",
            "card_border": "rgba(148,163,184,0.10)",
            "card_border_glow": "rgba(148,163,184,0.18)",
            "card_highlight": "rgba(255,255,255,0.02)",
            "glow_ring": "rgba(148,163,184,0.05)",
            "accent_from": "#94a3b8",
            "accent_to": "#7088a8",
            "edge_gradient_from": "#94a3b8",
            "edge_gradient_to": "#7088a8",
            "gradient_boost": 0.06,
        },
    },

    # ── Rose: rose gold + soft pink, for lifestyle / fashion / beauty ──
    "rose": {
        "meta": {"name": "玫瑰金粉", "mood": "温柔、精致、生活感"},
        "canvas": "#1a1018",
        "surface": "#2a1828",
        "text": "#e8c8d8",
        "text_dim": "#8a6078",
        "line": "#3a2038",
        "line_strong": "#6a3868",
        "categories": {
            "step":    {"fill": "#2a1028", "border": "#f472b6", "text": "#f0c8e0"},
            "start":   {"fill": "#182410", "border": "#a3e635", "text": "#c0d8a8"},
            "end":     {"fill": "#241020", "border": "#fb7185", "text": "#e8b8c0"},
            "decision":{"fill": "#241808", "border": "#fbbf24", "text": "#e8d098"},
            "data":    {"fill": "#1a1028", "border": "#e879f9", "text": "#d8b8f0"},
            "highlight":{"fill":"#201030", "border": "#c084fc", "text": "#e0c8f8"},
            "external":{"fill": "#181020", "border": "#483848", "text": "#a090a8"},
        },
        "subgraph": {"fill": "#0e0810", "border": "#2a1830", "text": "#6a3870"},
        "edges": {
            "main":     {"color": "#f472b6", "width": 2.5},
            "data":     {"color": "#e879f9", "width": 1.5},
            "feedback": {"color": "#fbbf24", "width": 1.5, "dash": "4,4"},
            "trigger":  {"color": "#fb7185", "width": 1.0, "dash": "2,4"},
        },
        "font": {"family": "system-ui, sans-serif", "size": 14},
        "effects": {
            "canvas_glow_top": "rgba(244,114,182,0.06)",
            "canvas_glow_bottom": "rgba(232,121,249,0.04)",
            "card_bg_start": "rgba(24,14,22,0.88)",
            "card_bg_end": "rgba(36,20,34,0.88)",
            "card_border": "rgba(244,114,182,0.12)",
            "card_border_glow": "rgba(244,114,182,0.22)",
            "card_highlight": "rgba(255,255,255,0.03)",
            "glow_ring": "rgba(244,114,182,0.06)",
            "accent_from": "#f472b6",
            "accent_to": "#e879f9",
            "edge_gradient_from": "#f472b6",
            "edge_gradient_to": "#e879f9",
            "gradient_boost": 0.18,
        },
    },
}

MERMAID_CDN = "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"

# ═══════════════════════════════════════════════════════════════
# Card Visual Style Presets — 4 distinct container treatments
# ═══════════════════════════════════════════════════════════════

CARD_STYLES = {
    # ── Glass: glassmorphism card (default) ──
    "glass": {
        "name": "玻璃拟态",
        "desc": "半透明模糊卡片，适合科技/现代/AI教程",
        # Background
        "body_bg_extra": (
            "radial-gradient(ellipse at 50% 0%, {glow_top} 0%, transparent 60%),\n"
            "      radial-gradient(ellipse at 80% 100%, {glow_bottom} 0%, transparent 50%)"
        ),
        "body_bg_only": "{bg}",
        # Card
        "card_bg_css": "linear-gradient(135deg, {card_bg_start}, {card_bg_end})",
        "card_backdrop": (
            "backdrop-filter: blur(16px);\n"
            "    -webkit-backdrop-filter: blur(16px);"
        ),
        "card_shadow_css": (
            "0 8px 40px {shadow_heavy},\n"
            "      0 2px 8px {shadow_light},\n"
            "      inset 0 1px 0 {card_highlight}"
        ),
        "card_border_css": "1px solid {card_border}",
        "card_radius": "20px",
        # Decorations
        "dot_grid_size": 12,          # 0 = no dots
        "dot_color_dark": "rgba(255,255,255,0.08)",
        "dot_color_light": "rgba(0,0,0,0.06)",
        "accent_line": "gradient",    # "gradient" | "solid" | "none"
        "accent_line_width": 60,      # px
        "accent_line_height": 2,      # px
        # Padding
        "card_pad_default": 48,       # px
        # SVG effects
        "node_gradient_boost": 0.18,
        "node_gradient": True,
        "node_shadow": True,
        "node_shadow_extra": True,    # second lighter shadow
        "node_glow": False,
        "edge_gradient": True,
    },

    # ── Solid: clean opaque card for business / formal ──
    "solid": {
        "name": "实色卡片",
        "desc": "纯色卡片+单层阴影，适合商务/正式/数据报告",
        "body_bg_extra": "",          # no radial glow
        "body_bg_only": "{bg}",
        "card_bg_css": "{surface}",
        "card_backdrop": "",
        "card_shadow_css": "0 4px 24px {shadow_heavy}",
        "card_border_css": "1px solid {line}",
        "card_radius": "12px",
        "dot_grid_size": 0,           # no dots
        "accent_line": "solid",
        "accent_line_width": 40,
        "accent_line_height": 2,
        "card_pad_default": 48,
        "node_gradient_boost": 0.08,
        "node_gradient": True,
        "node_shadow": True,
        "node_shadow_extra": False,
        "node_glow": False,
        "edge_gradient": False,
    },

    # ── Neon: high-contrast glow for creative / gaming ──
    "neon": {
        "name": "霓虹辉光",
        "desc": "强发光边框+节点辉光，适合创意/游戏/潮流内容",
        "body_bg_extra": (
            "radial-gradient(ellipse at 50% 0%, {glow_strong_top} 0%, transparent 50%),\n"
            "      radial-gradient(ellipse at 80% 100%, {glow_strong_bottom} 0%, transparent 50%)"
        ),
        "body_bg_only": "{bg}",
        "card_bg_css": "linear-gradient(135deg, {card_bg_start}, {card_bg_end})",
        "card_backdrop": (
            "backdrop-filter: blur(20px);\n"
            "    -webkit-backdrop-filter: blur(20px);"
        ),
        "card_shadow_css": (
            "0 8px 48px {shadow_heavy},\n"
            "      0 2px 12px {shadow_light},\n"
            "      0 0 24px {glow_ring},\n"
            "      inset 0 1px 0 {card_highlight}"
        ),
        "card_border_css": "1px solid {card_border_glow}",
        "card_radius": "20px",
        "dot_grid_size": 16,
        "dot_color_dark": "rgba(255,255,255,0.12)",
        "dot_color_light": "rgba(0,0,0,0.10)",
        "accent_line": "gradient",
        "accent_line_width": 80,
        "accent_line_height": 2,
        "card_pad_default": 48,
        "node_gradient_boost": 0.25,
        "node_gradient": True,
        "node_shadow": True,
        "node_shadow_extra": True,
        "node_glow": True,            # feGaussianBlur outer glow
        "edge_gradient": True,
    },

    # ── Minimal: ultra-clean, thin border, no decorations ──
    "minimal": {
        "name": "极简留白",
        "desc": "细线边框+呼吸感留白，适合文学/生活方式/高端品牌",
        "body_bg_extra": "",
        "body_bg_only": "{bg}",
        "card_bg_css": "{surface}",
        "card_backdrop": "",
        "card_shadow_css": "0 1px 4px {shadow_heavy}",
        "card_border_css": "1px solid {line}",
        "card_radius": "8px",
        "dot_grid_size": 0,
        "accent_line": "none",
        "accent_line_width": 0,
        "accent_line_height": 0,
        "card_pad_default": 56,       # more breathing room
        "node_gradient_boost": 0.0,
        "node_gradient": False,
        "node_shadow": False,
        "node_shadow_extra": False,
        "node_glow": False,
        "edge_gradient": False,
    },
}


# ── Shape to Mermaid mapping ──

_SHAPE_MAP = {
    "rounded":    '("{t}")',      # () rounded rectangle
    "rectangle":  '["{t}"]',      # [] sharp rectangle
    "stadium":    '(["{t}"])',    # ([]) stadium (pill)
    "subroutine": '[["{t}"]]',    # [[]] subroutine
    "cylinder":   '[("{t}")]',    # [()] database
    "diamond":    '{{"{t}"}}',    # {} diamond
    "hexagon":    '{{{{"{t}"}}}}', # {{}} hexagon
    "circle":     '(("{t}"))',    # (()) circle
}


# ═══════════════════════════════════════════════════════════════
# Mermaid Markup Generation
# ═══════════════════════════════════════════════════════════════

def _node_style(nid: str, node: dict, palette: dict) -> str:
    """Generate a per-node `style` directive from the category palette tokens.

    NOTE: We use per-node `style` directives instead of `classDef` because
    Mermaid v11.12+ has a parser regression that breaks classDef (syntax error).
    Per-node `style` is more verbose but reliably supported.
    """
    cat = node.get("category", "step")
    tokens = palette["categories"].get(cat, palette["categories"]["step"])
    return (
        f"  style {nid}"
        f" fill:{tokens['fill']},stroke:{tokens['border']},"
        f"color:{tokens['text']},stroke-width:2px"
    )


def _node_def(node: dict, palette: dict | None = None) -> str:
    """Generate a Mermaid node definition with optional icon and description.

    Uses ONLY Mermaid-native HTML (no <span> with custom styles) to ensure
    Mermaid's layout engine correctly measures text and sizes nodes.
    """
    nid = node["id"]
    label = node.get("label", nid)
    desc = node.get("desc", "")
    icon = node.get("icon", "")
    shape = node.get("shape", "rounded")

    # Escape single quotes; convert \n → <br/> for proper multi-line
    label_safe = label.replace("'", "&#39;")
    desc_safe = desc.replace("'", "&#39;").replace("\n", "<br/>") if desc else ""

    # Build rich label using only Mermaid-native formatting (no custom font sizes)
    # This ensures Mermaid's layout engine accurately measures text dimensions
    parts = []
    if icon:
        parts.append(f"<b>{icon}</b>")
    parts.append(f"<b>{label_safe}</b>")
    text = " ".join(parts)
    if desc_safe:
        text += f"<br/>{desc_safe}"

    template = _SHAPE_MAP.get(shape, _SHAPE_MAP["rounded"])
    return f"""{nid}{template.format(t=text)}"""


def _edge_def(edge: dict) -> str:
    """Return (edge_line, link_style_line_or_none) for an edge."""
    frm = edge["from"]
    to = edge["to"]
    label = edge.get("label", "")
    category = edge.get("category", "main")

    edge_spec = {
        "main":     "-->",
        "data":     "-->",
        "feedback": "-.->",
        "trigger":  "-.->",
    }.get(category, "-->")

    if label:
        line = f"  {frm} {edge_spec} |\"{label}\"| {to}"
    else:
        line = f"  {frm} {edge_spec} {to}"

    return line


def _theme_init(palette_name: str) -> str:
    """Generate YAML frontmatter config block.

    Uses YAML format (---/---) for Mermaid config. The %%{init}%% JSON format
    is avoided because it conflicts with advanced features in Mermaid v11.
    """
    p = PALETTES.get(palette_name, PALETTES["tech-dark"])
    c = p["categories"]["step"]
    sub = p["subgraph"]
    font = p["font"]

    return f"""---
config:
  theme: base
  themeVariables:
    background: "{p['canvas']}"
    primaryColor: "{c['fill']}"
    primaryBorderColor: "{c['border']}"
    primaryTextColor: "{c['text']}"
    secondaryColor: "{p['surface']}"
    secondaryBorderColor: "{p['line']}"
    tertiaryColor: "{p['canvas']}"
    tertiaryBorderColor: "{p['line']}"
    lineColor: "{p['line_strong']}"
    edgeLabelBackground: "{p['surface']}"
    noteBkgColor: "{sub['fill']}"
    noteBorderColor: "{sub['border']}"
    fontFamily: "{font['family']}"
    fontSize: "{font['size']}px"
  flowchart:
    useMaxWidth: false
    htmlLabels: true
    curve: basis
    padding: 36
---"""


def generate_mermaid(flow: dict, palette_name: str = "tech-dark") -> str:
    """Convert a flow dict to complete Mermaid.js markup with full design system.

    Uses per-node `style` directives instead of `classDef` (broken in Mermaid v11.12+).
    """
    p = PALETTES.get(palette_name, PALETTES["tech-dark"])
    direction = flow.get("direction", "LR")
    title = flow.get("title", "")
    nodes = flow.get("nodes", [])
    edges = flow.get("edges", [])
    subgraphs = flow.get("subgraphs", [])

    lines = []

    # 1. Theme init (YAML frontmatter)
    lines.append(_theme_init(palette_name))
    lines.append("")

    # 2. Flowchart direction
    lines.append(f"flowchart {direction}")
    lines.append("")

    # 3. Build subgraph membership map
    sg_map = {}  # node_id → subgraph_index
    if subgraphs:
        for sg_idx, sg in enumerate(subgraphs):
            for nid in sg.get("nodes", []):
                sg_map[nid] = sg_idx

    # 5. Nodes + per-node style directives
    lines.append("  %% ── Nodes ──")
    sg_open = [False] * len(subgraphs) if subgraphs else []
    for node in nodes:
        nid = node["id"]
        if nid in sg_map:
            sg_idx = sg_map[nid]
            sg = subgraphs[sg_idx]
            sg_title = sg.get("title", "")
            sg_id = "SG_" + sg_title.replace(" ", "_").replace("/", "_").replace("-", "_")
            if not sg_open[sg_idx]:
                lines.append(f"  subgraph {sg_id} [\"{sg_title}\"]")
                sg_open[sg_idx] = True
            lines.append(f"    {_node_def(node, p)}")
            lines.append(f"    {_node_style(nid, node, p)}")
        else:
            lines.append(f"  {_node_def(node, p)}")
            lines.append(f"  {_node_style(nid, node, p)}")
    # Close open subgraphs
    for sg_idx, is_open in enumerate(sg_open):
        if is_open:
            sg = subgraphs[sg_idx]
            sg_title = sg.get("title", "")
            sg_id = "SG_" + sg_title.replace(" ", "_").replace("/", "_").replace("-", "_")
            lines.append("  end")
            lines.append(f"  style {sg_id} fill:{p['subgraph']['fill']},"
                        f"stroke:{p['subgraph']['border']},color:{p['subgraph']['text']},"
                        f"stroke-width:1px,stroke-dasharray:6 4")
    lines.append("")

    # 6. Edges
    lines.append("  %% ── Edges ──")
    edge_categories = []
    for edge in edges:
        line = _edge_def(edge)
        lines.append(line)
        edge_categories.append(edge.get("category", "main"))
    lines.append("")

    # 7. linkStyle directives
    if edge_categories:
        lines.append("  %% ── Edge styles ──")
        for i, ecat in enumerate(edge_categories):
            et = p["edges"].get(ecat, p["edges"]["main"])
            color = et["color"]
            width = et.get("width", 2)
            dash = et.get("dash")
            style_parts = [f"stroke:{color}", f"stroke-width:{width}px"]
            if dash:
                style_parts.append(f"stroke-dasharray:{dash}")
            lines.append(f"  linkStyle {i} {','.join(style_parts)}")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# HTML Builder — card-style-aware template generation
# ═══════════════════════════════════════════════════════════════


def _parse_rgba_alpha(rgba_str: str) -> float:
    """Extract alpha value from an rgba() color string."""
    m = re.search(r'[\d.]+(?=\s*\)\s*$)', rgba_str.strip())
    return float(m.group()) if m else 1.0


def _boost_rgba_alpha(rgba_str: str, multiplier: float) -> str:
    """Multiply the alpha channel of an rgba() color, clamped to [0,1]."""
    parts = [p.strip() for p in rgba_str.strip('rgba()').split(',')]
    if len(parts) >= 4:
        parts[3] = f'{min(float(parts[3]) * multiplier, 1.0):.2f}'
    return f'rgba({", ".join(parts)})'


def _build_html(*, palette, card_style, mermaid, cdn,
                chart_title="", chart_subtitle="",
                width=720, padding=32, card_padding=None, watermark=""):
    """Generate the complete HTML page with card-style-aware CSS.

    All visual decisions flow from {palette × card_style}. The template
    is a single format string with conditional blocks keyed by card_style flags.
    """

    p = palette
    fx = p.get("effects", {})
    cs = CARD_STYLES.get(card_style, CARD_STYLES["glass"])

    # ── Compute all template parameters ──

    bg = p["canvas"]
    surface = p["surface"]
    line_color = p["line"]
    text_dim = p["text_dim"]

    is_light = (p.get("meta", {}).get("name", "") == "宣纸白" or
                p.get("canvas", "").startswith("#f"))

    # Shadows
    if is_light:
        shadow_heavy = "rgba(0,0,0,0.05)"
        shadow_light = "rgba(0,0,0,0.04)"
        dot_color = cs.get("dot_color_light", "rgba(0,0,0,0.06)")
    else:
        shadow_heavy = "rgba(0,0,0,0.40)"
        shadow_light = "rgba(0,0,0,0.20)"
        dot_color = cs.get("dot_color_dark", "rgba(255,255,255,0.08)")

    title_text = "#f1f5f9" if not is_light else "#1a1a2e"

    # Card background
    card_bg_start = fx.get("card_bg_start", p["surface"])
    card_bg_end = fx.get("card_bg_end", p["surface"])
    card_border = fx.get("card_border", p["line"])
    card_highlight = fx.get("card_highlight", "rgba(255,255,255,0.02)")

    # Accent line
    accent_from = fx.get("accent_from", p["categories"]["step"]["border"])
    accent_to = fx.get("accent_to", accent_from)

    # Neon-specific: boosted glow colors
    glow_top = fx.get("canvas_glow_top", "transparent")
    glow_bottom = fx.get("canvas_glow_bottom", "transparent")
    glow_strong_top = _boost_rgba_alpha(glow_top, 2.0) if glow_top != "transparent" else "transparent"
    glow_strong_bottom = _boost_rgba_alpha(glow_bottom, 2.0) if glow_bottom != "transparent" else "transparent"
    card_border_glow = fx.get("card_border_glow",
                              _boost_rgba_alpha(card_border, 1.8))
    glow_ring = fx.get("glow_ring", card_border)

    # Body background
    if cs["body_bg_extra"] and card_style == "neon":
        body_bg_image = cs["body_bg_extra"].format(
            glow_strong_top=glow_strong_top,
            glow_strong_bottom=glow_strong_bottom)
        body_bg = f"{cs['body_bg_only'].format(bg=bg)};\n    background-image:\n      {body_bg_image}"
    elif cs["body_bg_extra"]:
        body_bg_image = cs["body_bg_extra"].format(
            glow_top=glow_top, glow_bottom=glow_bottom)
        body_bg = f"{cs['body_bg_only'].format(bg=bg)};\n    background-image:\n      {body_bg_image}"
    else:
        body_bg = bg

    # Card shadow
    card_shadow = cs["card_shadow_css"].format(
        shadow_heavy=shadow_heavy,
        shadow_light=shadow_light,
        card_highlight=card_highlight,
        glow_ring=glow_ring)

    # Card border
    if card_style == "neon":
        card_border_css = cs["card_border_css"].format(card_border_glow=card_border_glow)
    else:
        card_border_css = cs["card_border_css"].format(
            card_border=card_border, line=line_color)

    # Card radius
    card_radius = cs["card_radius"]

    # Backdrop
    card_backdrop = cs["card_backdrop"]

    # Card background CSS
    card_bg_css = cs["card_bg_css"].format(
        card_bg_start=card_bg_start, card_bg_end=card_bg_end,
        surface=surface)

    # Padding
    card_pad = card_padding if card_padding is not None else cs["card_pad_default"]
    max_width = width - padding * 2

    # ── Dot decoration ──
    dot_css = ""
    if cs["dot_grid_size"] > 0:
        gs = cs["dot_grid_size"]
        dot_css = f"""
      .chart-card::before {{
        content: '';
        position: absolute;
        top: 18px;
        left: 18px;
        width: {gs * 3}px;
        height: {gs * 3}px;
        background-image:
          radial-gradient(circle, {dot_color} 1px, transparent 1px);
        background-size: {gs}px {gs}px;
        pointer-events: none;
      }}"""

    # ── Accent line ──
    accent_line_css = ""
    if cs["accent_line"] == "gradient":
        w_ = cs["accent_line_width"]
        h_ = cs["accent_line_height"]
        accent_line_css = f"""
      .accent-line {{
        display: block;
        width: {w_}px;
        height: {h_}px;
        margin: 0 auto;
        border-radius: 1px;
        background: linear-gradient(90deg, {accent_from}, {accent_to}, transparent);
      }}"""
    elif cs["accent_line"] == "solid":
        w_ = cs["accent_line_width"]
        h_ = cs["accent_line_height"]
        accent_line_css = f"""
      .accent-line {{
        display: block;
        width: {w_}px;
        height: {h_}px;
        margin: 0 auto;
        border-radius: 1px;
        background: {accent_from};
      }}"""

    # ── Title block ──
    if chart_title:
        title_block = f"""<div class="chart-title-block">
        <h1 class="chart-title">{chart_title}</h1>
        <p class="chart-subtitle">{chart_subtitle}</p>
        <span class="accent-line"></span>
      </div>"""
    else:
        title_block = ""

    # ── Watermark ──
    if not watermark:
        pmeta = p.get("meta", {})
        watermark = f"{pmeta.get('name', '')} · {pmeta.get('mood', '')}"

    # ── Assemble HTML ──
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    background: {body_bg};
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: {padding}px;
    font-family: "Segoe UI", "Microsoft YaHei", system-ui, -apple-system, sans-serif;
  }}

  /* ── Card wrapper ── */
  .chart-card {{
    background: {card_bg_css};
    {card_backdrop}
    border-radius: {card_radius};
    padding: {card_pad}px;
    max-width: {max_width}px;
    width: 100%;
    box-shadow:
      {card_shadow};
    border: {card_border_css};
    position: relative;
    overflow: hidden;
  }}
{dot_css}
  /* ── Title block ── */
  .chart-title-block {{
    text-align: center;
    margin-bottom: 28px;
  }}
  .chart-title {{
    font-size: 22px;
    font-weight: 700;
    color: {title_text};
    letter-spacing: 0.02em;
    margin: 0 0 6px 0;
    line-height: 1.3;
  }}
  .chart-subtitle {{
    font-size: 13px;
    color: {text_dim};
    letter-spacing: 0.04em;
    margin: 0 0 14px 0;
    line-height: 1.4;
  }}
{accent_line_css}
  /* ── Mermaid container ── */
  .mermaid {{
    display: flex;
    justify-content: center;
    align-items: center;
  }}

  .mermaid svg {{
    max-width: 100%;
    height: auto;
  }}

  /* ── Watermark badge ── */
  .watermark {{
    margin-top: 16px;
    text-align: center;
    font-size: 10px;
    color: {text_dim};
    letter-spacing: 0.05em;
    opacity: 0.4;
  }}
</style>
</head>
<body>
<div class="chart-card">
  {title_block}
  <pre class="mermaid">
{mermaid}
  </pre>
</div>
<div class="watermark">{watermark}</div>
<script src="{cdn}"></script>
<script>
  mermaid.initialize({{ startOnLoad: true }});
</script>
</body>
</html>"""
    return html


def _build_svg_postprocess_js(*, node_gradients, edge_grad,
                               node_gradient, node_shadow, node_shadow_extra,
                               node_glow, edge_gradient, node_border_color):
    """Build the JS string for SVG post-processing, conditioned on style flags.

    This avoids string concat in the hot path — all logic is in this builder.
    The JS is injected via page.evaluate() after Mermaid renders.
    """
    import json as _json
    ng_json = _json.dumps(node_gradients)
    eg_json = _json.dumps(edge_grad)

    # ── Build JS blocks conditionally ──
    js_parts = ["""() => {
        const svg = document.querySelector('.mermaid svg');
        if (!svg) return;
        const NS = 'http://www.w3.org/2000/svg';

        // Get or create <defs>
        let defs = svg.querySelector('defs');
        if (!defs) {
            defs = document.createElementNS(NS, 'defs');
            svg.insertBefore(defs, svg.firstChild);
        }"""]

    # Shadow filter
    if node_shadow:
        if node_shadow_extra:
            shadow_html = ('<feDropShadow dx="0" dy="3" stdDeviation="4" flood-color="#000" flood-opacity="0.35"/>'
                           '<feDropShadow dx="0" dy="1" stdDeviation="1.5" flood-color="#000" flood-opacity="0.18"/>')
        else:
            shadow_html = '<feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#000" flood-opacity="0.25"/>'
        js_parts.append(f"""
        // ── Shadow filter ──
        const shadowFilter = document.createElementNS(NS, 'filter');
        shadowFilter.setAttribute('id', 'fc-shadow');
        shadowFilter.setAttribute('x', '-20%');
        shadowFilter.setAttribute('y', '-20%');
        shadowFilter.setAttribute('width', '140%');
        shadowFilter.setAttribute('height', '140%');
        shadowFilter.innerHTML = '{shadow_html}';
        defs.appendChild(shadowFilter);""")

    # Glow filter (neon style)
    if node_glow:
        glow_color = node_border_color
        js_parts.append(f"""
        // ── Glow filter ──
        const glowFilter = document.createElementNS(NS, 'filter');
        glowFilter.setAttribute('id', 'fc-glow');
        glowFilter.setAttribute('x', '-30%');
        glowFilter.setAttribute('y', '-30%');
        glowFilter.setAttribute('width', '160%');
        glowFilter.setAttribute('height', '160%');
        glowFilter.innerHTML = '<feGaussianBlur stdDeviation="3.5" result="blur"/>'
          + '<feFlood flood-color="{glow_color}" flood-opacity="0.25" result="color"/>'
          + '<feComposite in="color" in2="blur" operator="in" result="glow"/>'
          + '<feMerge><feMergeNode in="glow"/><feMergeNode in="SourceGraphic"/></feMerge>';
        defs.appendChild(glowFilter);""")

    # Edge gradient
    if edge_gradient:
        js_parts.append(f"""
        // ── Edge gradient ──
        const edgeGrad = {eg_json};
        const edgeGradient = document.createElementNS(NS, 'linearGradient');
        edgeGradient.setAttribute('id', 'fc-edge-grad');
        edgeGradient.setAttribute('x1', '0'); edgeGradient.setAttribute('y1', '0');
        edgeGradient.setAttribute('x2', '1'); edgeGradient.setAttribute('y2', '0');
        edgeGradient.innerHTML = '<stop offset="0%" stop-color="' + edgeGrad.from + '"/><stop offset="100%" stop-color="' + edgeGrad.to + '"/>';
        defs.appendChild(edgeGradient);""")

    # ForeignObject overflow fix (always needed)
    js_parts.append("""
        // ── Fix foreignObject overflow ──
        svg.querySelectorAll('foreignObject').forEach(fo => {
            const div = fo.querySelector('div');
            if (!div) return;
            const scrollW = div.scrollWidth;
            const attrW = parseFloat(fo.getAttribute('width')) || 0;
            const extra = scrollW - attrW;
            if (extra > 2) {
                fo.setAttribute('width', String(scrollW));
                const labelG = fo.closest('g.label');
                if (labelG) {
                    const t = labelG.getAttribute('transform') || '';
                    const m = t.match(/translate\\(([^,]+),\\s*([^)]+)\\)/);
                    if (m) {
                        labelG.setAttribute('transform',
                            'translate(' + (parseFloat(m[1]) - extra/2) + ', ' + m[2] + ')');
                    }
                }
            }
        });""")

    # Node gradient fills + filters
    js_parts.append(f"""
        // ── Apply node effects ──
        const nodeRects = svg.querySelectorAll('.node:not(.cluster) rect.basic');
        const nodeGradients = {ng_json};
        const catKeys = Object.keys(nodeGradients);""")

    if node_gradient or node_shadow or node_glow:
        js_parts.append("""
        nodeRects.forEach((rect, i) => {
            const catKey = catKeys[i % catKeys.length] || 'step';
            const gc = nodeGradients[catKey];""")

        if node_gradient and node_gradients:
            js_parts.append("""
            if (gc) {
                const gradId = 'fc-node-grad-' + i;
                const grad = document.createElementNS(NS, 'linearGradient');
                grad.setAttribute('id', gradId);
                grad.setAttribute('x1', '0'); grad.setAttribute('y1', '0');
                grad.setAttribute('x2', '0'); grad.setAttribute('y2', '1');
                grad.innerHTML = '<stop offset="0%" stop-color="' + gc.top + '"/><stop offset="100%" stop-color="' + gc.bottom + '"/>';
                defs.appendChild(grad);
                rect.setAttribute('fill', 'url(#' + gradId + ')');
            }""")

        if node_shadow or node_glow:
            filter_parts = []
            if node_shadow:
                filter_parts.append("url(#fc-shadow)")
            if node_glow:
                filter_parts.append("url(#fc-glow)")
            filter_str = " ".join(filter_parts)
            js_parts.append(f"""
            rect.setAttribute('filter', '{filter_str}');""")

        js_parts.append("""
        });""")

    # Edge effects
    js_parts.append("""
        // ── Apply edge effects ──
        const edgePaths = svg.querySelectorAll('.flowchart-link');""")

    if edge_gradient:
        js_parts.append("""
        edgePaths.forEach(path => {
            path.setAttribute('stroke', 'url(#fc-edge-grad)');
        });

        // Color the arrowhead markers to match edge gradient end
        const arrowPaths = svg.querySelectorAll('marker[id*="pointEnd"] .arrowMarkerPath, marker[id*="pointEnd"] path');
        arrowPaths.forEach(p => {
            p.setAttribute('stroke', edgeGrad.to);
            p.setAttribute('fill', edgeGrad.to);
        });""")

    js_parts.append("\n    }")
    return "\n".join(js_parts)


def _hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex color to (r,g,b) tuple."""
    h = hex_color.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb: tuple) -> str:
    """Convert (r,g,b) tuple to #rrggbb."""
    return '#{:02x}{:02x}{:02x}'.format(*rgb)


def _lighten_hex(hex_color: str, amount: float) -> str:
    """Lighten (amount>0) or darken (amount<0) a hex color."""
    r, g, b = _hex_to_rgb(hex_color)
    if amount >= 0:
        r = min(255, int(r + (255 - r) * amount))
        g = min(255, int(g + (255 - g) * amount))
        b = min(255, int(b + (255 - b) * amount))
    else:
        r = max(0, int(r * (1 + amount)))
        g = max(0, int(g * (1 + amount)))
        b = max(0, int(b * (1 + amount)))
    return _rgb_to_hex((r, g, b))


def render_mermaid_to_png(mermaid_markup: str, output_path: str,
                          palette_name: str = "tech-dark",
                          card_style: str = "glass",
                          width: int = 720, device_scale: float = 2.0,
                          padding: int = 32, card_padding: int = None,
                          watermark: str = "",
                          chart_title: str = "",
                          chart_subtitle: str = ""):
    """Render Mermaid markup → styled card PNG via Playwright.

    Args:
        mermaid_markup:  Complete Mermaid.js markup
        output_path:     Output PNG path
        palette_name:    Design palette key (13 palettes available)
        card_style:      Visual card style: glass|solid|neon|minimal
        width:           Viewport width (canvas)
        device_scale:    Retina multiplier (2.0 = crisp on HiDPI)
        padding:         Outer page padding
        card_padding:    Inner card padding (None = use style default)
        watermark:       Optional footer text
        chart_title:     Title displayed in the card header
        chart_subtitle:  Subtitle displayed below the title
    """
    if not HAS_PLAYWRIGHT:
        print("ERROR: playwright not installed. pip install playwright && playwright install chromium")
        sys.exit(1)

    p = PALETTES.get(palette_name, PALETTES["tech-dark"])
    cs = CARD_STYLES.get(card_style, CARD_STYLES["glass"])
    fx = p.get("effects", PALETTES["tech-dark"]["effects"])

    # ── Build HTML using the card-style-aware builder ──
    html = _build_html(
        palette=p, card_style=card_style,
        mermaid=mermaid_markup, cdn=MERMAID_CDN,
        chart_title=chart_title, chart_subtitle=chart_subtitle,
        width=width, padding=padding,
        card_padding=card_padding, watermark=watermark)

    # ── Pre-compute SVG post-processing parameters ──
    boost = cs["node_gradient_boost"]
    node_gradients = {}
    if cs["node_gradient"] and boost != 0:
        for cat_key, cat in p["categories"].items():
            node_gradients[cat_key] = {
                "top": _lighten_hex(cat["fill"], boost),
                "bottom": cat["fill"],
                "border": cat["border"],
            }
    edge_grad = {
        "from": fx["edge_gradient_from"],
        "to": fx["edge_gradient_to"],
    }

    # ── Build style-aware SVG post-processing JS ──
    svg_js = _build_svg_postprocess_js(
        node_gradients=node_gradients,
        edge_grad=edge_grad,
        node_gradient=cs["node_gradient"],
        node_shadow=cs["node_shadow"],
        node_shadow_extra=cs["node_shadow_extra"],
        node_glow=cs["node_glow"],
        edge_gradient=cs["edge_gradient"],
        node_border_color=fx.get("accent_from", p["categories"]["step"]["border"]))

    with tempfile.NamedTemporaryFile(suffix=".html", mode="w", encoding="utf-8", delete=False) as f:
        f.write(html)
        html_path = f.name

    try:
        with sync_playwright() as pobj:
            browser = pobj.chromium.launch(headless=True)
            page = browser.new_page(
                viewport={"width": width, "height": 900},
                device_scale_factor=device_scale,
            )
            page.goto(f"file:///{html_path.replace(os.sep, '/')}",
                      wait_until="networkidle", timeout=30000)

            # Wait for Mermaid SVG
            page.wait_for_selector(".mermaid svg", timeout=15000)
            page.wait_for_timeout(800)  # extra render settling

            # ── Post-processing: foreignObject overflow + SVG effects ──
            page.evaluate(svg_js)

            # Screenshot the card, not the full page (focus on content)
            card = page.locator(".chart-card")
            if card.count() > 0:
                card.screenshot(path=output_path)
            else:
                page.screenshot(path=output_path, full_page=True)

            browser.close()
    finally:
        os.unlink(html_path)


# ═══════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════

def generate_flowchart(flow: str | dict, output_path: str,
                       palette: str = "tech-dark", style: str = "glass",
                       width: int = 720):
    """End-to-end: flow dict/JSON → design-grade PNG.

    Args:
        flow:        Flow dict or JSON string
        output_path: Output PNG path
        palette:     Design palette key (13 palettes available)
        style:       Visual card style: glass|solid|neon|minimal
        width:       Canvas width in pixels
    """
    if isinstance(flow, str):
        flow = json.loads(flow)

    # Use flow-level palette/style overrides if specified
    flow_palette = flow.get("palette", palette)
    flow_style = flow.get("style", style)
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    markup = generate_mermaid(flow, flow_palette)
    render_mermaid_to_png(
        markup, output_path,
        palette_name=flow_palette, card_style=flow_style, width=width,
        chart_title=flow.get("title", ""),
        chart_subtitle=flow.get("desc", ""),
    )

    size_kb = os.path.getsize(output_path) / 1024
    pmeta = PALETTES.get(flow_palette, PALETTES["tech-dark"])["meta"]
    smeta = CARD_STYLES.get(flow_style, CARD_STYLES["glass"])
    print(f"OK: {output_path} ({size_kb:.1f} KB) "
          f"palette:{flow_palette} ({pmeta['name']}) "
          f"style:{flow_style} ({smeta['name']})")


def list_palettes():
    """Print available palettes and card styles."""
    print("Available design palettes:\n")
    palette_count = len(PALETTES)
    for key, p in PALETTES.items():
        meta = p["meta"]
        print(f"  {key:14s}  {meta['name']:6s}  {meta['mood']}")
    print(f"\n  ── {palette_count} palettes total")

    print("\nAvailable card styles:\n")
    for key, cs in CARD_STYLES.items():
        print(f"  {key:10s}  {cs['name']:6s}  {cs['desc']}")
    print(f"\n  ── {palette_count} palettes × {len(CARD_STYLES)} styles = {palette_count * len(CARD_STYLES)} unique looks")


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def main():
    # Fix Windows GBK stdout for emoji output
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    p = argparse.ArgumentParser(
        description="Design-grade flowcharts for WeChat tutorials (Mermaid.js + Playwright)")

    p.add_argument("--file", help="JSON file with flow definition")
    p.add_argument("--inline", help="Inline JSON flow definition")
    p.add_argument("--output", "-o", help="Output PNG path")
    p.add_argument("--palette", choices=list(PALETTES.keys()), default="tech-dark",
                   help="Design palette (13 options, see --list-palettes)")
    p.add_argument("--style", "-s", choices=list(CARD_STYLES.keys()), default="glass",
                   help="Card visual style: glass|solid|neon|minimal")
    p.add_argument("--width", type=int, default=720,
                   help="Canvas width in px (default: 720)")
    p.add_argument("--markup-only", action="store_true",
                   help="Print Mermaid markup only (debug, no output required)")
    p.add_argument("--list-palettes", action="store_true",
                   help="Show available palettes & card styles and exit")

    args = p.parse_args()

    if args.list_palettes:
        list_palettes()
        return

    if args.markup_only:
        if args.file:
            with open(args.file, "r", encoding="utf-8") as f:
                flow = json.load(f)
        elif args.inline:
            flow = json.loads(args.inline)
        else:
            p.error("Either --file or --inline is required")
        print(generate_mermaid(flow, args.palette))
        return

    if not args.output:
        p.error("--output/-o is required for rendering")

    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            flow = json.load(f)
    elif args.inline:
        flow = json.loads(args.inline)
    else:
        p.error("Either --file or --inline is required")

    generate_flowchart(flow, args.output, palette=args.palette, style=args.style, width=args.width)


if __name__ == "__main__":
    main()
