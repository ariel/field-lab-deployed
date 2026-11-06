"""Explicit local workflow switches; no cloud dependencies."""
import json
from .guards import ROOT
DEFAULTS={'automatic_face_grouping':True,'automatic_voice_grouping':True,'automatic_note_inheritance':True,'face_named_match_threshold':.72,'identity_match_margin':.08}
def features():
 try:return {**DEFAULTS,**json.loads((ROOT/'config.json').read_text()).get('features',{})}
 except (OSError,ValueError):return dict(DEFAULTS)
