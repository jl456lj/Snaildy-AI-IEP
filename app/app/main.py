from . import RAG, LLM
from typing import List, Union, Annotated
from fastapi import FastAPI, Form
from pydantic import BaseModel
from fastapi.responses import FileResponse


app = FastAPI()

class SenCategory(BaseModel):
    unconfirmed: List[str] | None = None
    confirmed: List[str] | None = None

class UserRequest(BaseModel):
    name: str
    className: str
    senCategoryUnconfirmed: Union[List[str],str]
    senCategoryConfirmed: Union[List[str],str]
    gradeAge: str
    strengthsWeaknesses: Union[List[str], str]

@app.post("/")
async def IEP_Report(UserRequest: Annotated[UserRequest,Form()]):
    student_context = f"""
    【基本資料】
    - 姓名: {UserRequest.name}
    - 年級/年齡: {UserRequest.className} / {UserRequest.gradeAge}

    【特殊教育需要 (SEN) 狀況】
    - 未確定: {UserRequest.senCategoryUnconfirmed}
    - 已確定: {UserRequest.senCategoryUnconfirmed}
        

    【強弱項與性格描述】
    {UserRequest.strengthsWeaknesses}

    """
    golden_context = RAG.retrieve_context_with_reranking(student_context)
    final_report = LLM.generate_final_iep(student_context, golden_context)

    if final_report:
        json_string = final_report.model_dump_json(indent=2, ensure_ascii=False)
        file_name = f"{UserRequest.name}_IEP.json"
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(json_string)
    return FileResponse(
        file_name,
        media_type="application/json",
        filename=file_name
        )
    
