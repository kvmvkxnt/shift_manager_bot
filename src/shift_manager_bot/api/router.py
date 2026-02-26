from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shift_manager_bot.api.routes import users, shifts, tasks


app = FastAPI(title="Shift Manager API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(shifts.router, prefix="/api/shifts", tags=["shifts"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
