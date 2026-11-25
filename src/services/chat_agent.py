import asyncio
import os
from collections.abc import Awaitable, Callable
from typing import Annotated

from dotenv import load_dotenv
from haystack.components.agents import Agent
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.dataclasses import ChatMessage, ChatRole, StreamingChunk
from haystack.tools import SkillToolset, tool
from haystack.utils import Secret
from nicemvvm.tools.messenger import Messenger

from services.chat_tools import get_current_time
from services.pg_skill_store import PgSkillStore
from src.services.mojeek_search import create_mojeek_search_tool
from src.services.rag_service import RagService
from src.services.user import get_org_id

SYSTEM_PROMPT = (
    "\n"
    "You are a deep research assistant.\n"
    "You create comprehensive research reports to answer the user's questions.\n"
    "You use the 'web_search' tool to answer any questions about topics "
    "you don't know about.\n"
    "You perform multiple searches until you have the information you need "
    "to answer the question.\n"
    "Make sure you research different aspects of the question.\n"
    "Use markdown to format your response.\n"
    "When you use information from the websearch results, cite your sources "
    "using markdown links.\n"
    "It is important that you cite accurately.\n"
)


@tool
def retrieve_org_id() -> int:
    """Retrieve the organization ID for the current user."""
    return get_org_id()


@tool
def search_knowledge_base(
    query: Annotated[
        str,
        "The search query or keywords to look up in the remote PostgreSQL "
        "knowledge base.",
    ],
    limit: Annotated[
        int, "Maximum number of relevant document passages to retrieve (default: 5)"
    ] = 5,
) -> str:
    """Search for relevant documents and text chunks in the remote PostgreSQL
    database using hybrid vector and keyword search."""
    rag_service = RagService()
    org_id = get_org_id()
    return asyncio.run(
        rag_service.search_and_format(org_id=org_id, query=query, limit=limit)
    )


@tool
def list_knowledge_base_documents(
    limit: Annotated[
        int, "Maximum number of document entries to list (default: 20)"
    ] = 20,
) -> str:
    """List all documents currently indexed in the remote PostgreSQL database."""
    rag_service = RagService()
    org_id = get_org_id()
    return asyncio.run(rag_service.list_documents_formatted(org_id=org_id, limit=limit))


@tool
def get_document_details(
    document_id: Annotated[int, "The numeric ID of the document to inspect in detail."],
) -> str:
    """Retrieve all content chunks and page details for a specific document
    by its ID."""
    rag_service = RagService()
    return asyncio.run(
        rag_service.get_document_details_formatted(document_id=document_id)
    )


class ChatAgent:
    def __init__(self):
        load_dotenv()
        self.messenger = Messenger()
        self.messages = [ChatMessage.from_system(SYSTEM_PROMPT)]
        self.task: asyncio.Task | None = None
        self.partial: list[str] = []
        self.org_id = get_org_id()
        self.rag_service = RagService()
        self.skills_toolset = SkillToolset(PgSkillStore(org_id=self.org_id))

        web_search = create_mojeek_search_tool(
            top_k=5,
            search_params={"lb": "EN", "lbb": 100, "dlen": 300},
            # allowed_domains=[".daimlertruck.com"],   # optional, max 25
            raise_on_failure=False,  # agent gets "No results found." instead of a crash
        )

        chat_generator = OpenAIChatGenerator(
            api_key=Secret.from_env_var("OPENAI_API_KEY"),
            model=os.getenv("AGENT_CHAT_MODEL") or "Qwen/Qwen3.8-27B",
            api_base_url=os.getenv("OPENAI_API_URL"),
            streaming_callback=self._streaming_callback,
        )
        self.agent = Agent(
            chat_generator=chat_generator,
            tools=[
                web_search,
                get_current_time,
                search_knowledge_base,
                list_knowledge_base_documents,
                get_document_details,
                self.skills_toolset,
            ],
            # max_agent_steps=10,
        )
        self.agent.warm_up()

    async def _streaming_callback(self, chunk: StreamingChunk) -> None:
        if chunk.content:
            self.partial.append(chunk.content)
        await self.messenger.broadcast("stream_reply", chunk=chunk)

    def subscribe(
        self, message: str, handler: Callable[..., None | Awaitable[None]]
    ) -> None:
        self.messenger.subscribe(message, handler)

    async def ask_async(self, prompt: str) -> None:
        user_msg = ChatMessage.from_user(prompt)
        self.messages.append(user_msg)
        self.partial.clear()
        self.task = asyncio.create_task(self.agent.run_async(messages=self.messages))

        try:
            if self.task:
                result = await self.task

                # result["messages"] holds the full turn: user msg, tool calls,
                # tool results and the final reply. Drop the system message, since
                # the Agent re-adds system_prompt on every run.
                self.messages = [
                    m for m in result["messages"] if not m.is_from(ChatRole.SYSTEM)
                ]

                await self.messenger.broadcast("reply", reply=self.messages[-1])

        except asyncio.CancelledError:
            cancel_message = ChatMessage.from_assistant(text="User interrupted.")
            await self.messenger.broadcast("reply", reply=cancel_message)

        # Keep the REPL alive on API/tool errors
        except Exception:  # noqa: BLE001
            self.messages.pop()

    def stop(self) -> None:
        if self.task and not self.task.done():
            self.task.cancel()
