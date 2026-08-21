import os

from dotenv import load_dotenv
from nicegui import ui, context, app

from src.viewmodels.AgentViewModel import AgentViewModel
from src.views.main_view import MainView


@ui.page("/")
def index():
    ui.add_css("""
    .custom-scroll-area .q-scrollarea__content {
        padding: 0px 12px 0px 4px !important;
        gap: 0px !important;
    }
    .edit-view-field .q-field {
        padding-top: 4px !important;
    }
    .small-menu .q-item {
        min-height: 24px;
        padding: 4px 8px;
        font-size: 12px;
    }
    """)

    context.client.content.classes("p-0")
    ui.page_title("Agent")
    # add_inactivity_timeout(300, logout)  # 5 minutes of inactivity
    MainView(AgentViewModel())



app.add_static_file(local_file=os.path.join(os.path.dirname(__file__), 'src/images', 'support_agent_24dp_1F1F1F.png'),
                    url_path='/favicon.ico')
load_dotenv()
ui.run(
    host="0.0.0.0",
    port=int(os.environ.get("PORT", 8080)),
    favicon="/favicon.ico",
    title="Agent",
    reload=True,
    storage_secret=os.environ.get("STORAGE_SECRET", "default_secret"),
)
