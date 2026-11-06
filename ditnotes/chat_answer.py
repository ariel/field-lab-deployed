"""Separate investigated candidates from the final answer's verified selection."""
from typing import Literal
from pydantic import BaseModel,Field

class VisualEvidence(BaseModel):
    result_id:str
    visible_support:str=Field(description='Concrete visible evidence for the requested setting/action; do not infer a shop from colorful decor alone.')

class ChatAnswer(BaseModel):
    outcome:Literal['matched','not_verified','explanation']
    answer:str=Field(description='Brief answer. Say not verified if any requested condition is unsupported; do not label unrelated alternatives as matches.')
    result_ids:list[str]=Field(description='Only final verified matching shots; MUST be empty for not_verified. These are not the candidate frames investigated.')
    visual_evidence:list[VisualEvidence]=Field(default_factory=list)

def legacy_unverified(answer):
    return answer.strip().casefold().startswith(("i couldn't verify a matching shot",'i could not verify a matching shot','i stopped this search before completing verification'))
