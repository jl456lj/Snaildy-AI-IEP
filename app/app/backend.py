from . import RAG, LLM
from fastapi import FastAPI
from pydantic import BaseModel



app = FastAPI()

class RequestData(BaseModel):
    context: str

@app.get("/")    #Check if fastapi is working
async def root():
    return {"message": "FastAPI backend is working."}

@app.post("/chat")   # IEP generation
async def IEP_Report(Request: RequestData):

    student_context = Request.context
    golden_context = RAG.retrieve_context_with_reranking(student_context)
    final_report = LLM.generate_final_iep(student_context, golden_context)

    return final_report
