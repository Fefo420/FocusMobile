import flet as ft
import requests
import asyncio
import random
from datetime import datetime

# --- CONFIGURATION ---
FIREBASE_URL = "https://productivity-71d06-default-rtdb.europe-west1.firebasedatabase.app/leaderboard.json"

# --- GLOBAL MEMORY ---
APP_DATA = {
    "username": "MobileUser",
    "tasks": []
}

def main(page: ft.Page):
    page.title = "Focus Companion"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 10
    # We handle scrolling inside the specific views
    page.scroll = None 

    # --- HELPERS ---
    def set_username(e):
        if e.control.value:
            APP_DATA["username"] = e.control.value
            page.snack_bar = ft.SnackBar(ft.Text(f"Username saved: {APP_DATA['username']}"))
            page.snack_bar.open = True
            page.update()

    def upload_session(minutes, task_name=None):
        data = {
            "username": APP_DATA["username"],
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "duration": f"{minutes} min",
            "tasks_done": [task_name] if task_name else [],
            "task_count": 1 if task_name else 0
        }
        try:
            requests.post(FIREBASE_URL, json=data)
            print("Uploaded to Firebase")
        except Exception as e:
            print(f"Upload failed: {e}")

    # ==========================================
    # VIEW 1: TIMER
    # ==========================================
    timer_txt = ft.Text("00:00", size=70, weight="bold", color=ft.Colors.BLUE_200)
    timer_input = ft.TextField(label="Minutes", width=100, keyboard_type=ft.KeyboardType.NUMBER)
    timer_btn = ft.FilledButton("START", style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600, color="white"))
    
    timer_state = {"running": False}
    
    async def run_timer(e):
        if timer_state["running"]: 
            timer_state["running"] = False
            timer_btn.text = "START"
            timer_btn.style = ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600, color="white")
            page.update()
            return

        try: mins = int(timer_input.value)
        except: return

        timer_state["running"] = True
        timer_btn.text = "STOP"
        timer_btn.style = ft.ButtonStyle(bgcolor=ft.Colors.RED_600, color="white")
        
        seconds = mins * 60
        initial_mins = mins
        
        while seconds > 0 and timer_state["running"]:
            m, s = divmod(seconds, 60)
            timer_txt.value = f"{m:02d}:{s:02d}"
            page.update()
            await asyncio.sleep(1)
            seconds -= 1
            
        if timer_state["running"] and seconds == 0:
            timer_txt.value = "DONE!"
            timer_state["running"] = False
            timer_btn.text = "START"
            timer_btn.style = ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600, color="white")
            upload_session(initial_mins)
            page.snack_bar = ft.SnackBar(ft.Text("Session Uploaded!"))
            page.snack_bar.open = True
        
        page.update()

    timer_btn.on_click = run_timer
    
    view_timer = ft.Column([
        ft.Text("Focus Timer", size=30, weight="bold"),
        ft.Divider(),
        ft.Row([timer_input, timer_btn], alignment="center"),
        ft.Container(height=50),
        timer_txt,
    ], horizontal_alignment="center", scroll="adaptive")

    # ==========================================
    # VIEW 2: TASKS
    # ==========================================
    task_input = ft.TextField(hint_text="Add a task...", expand=True)
    tasks_view = ft.ListView(expand=True, spacing=10)

    def render_tasks():
        tasks_view.controls.clear()
        for t in APP_DATA["tasks"]:
            tasks_view.controls.append(create_task_row(t))
        page.update()

    def add_task(e):
        if not task_input.value: return
        APP_DATA["tasks"].append({"text": task_input.value, "done": False})
        task_input.value = ""
        render_tasks()

    def delete_task(task_text):
        APP_DATA["tasks"] = [t for t in APP_DATA["tasks"] if t["text"] != task_text]
        render_tasks()

    def toggle_task(task_text, value):
        for t in APP_DATA["tasks"]:
            if t["text"] == task_text:
                t["done"] = value
                if value: 
                    upload_session(0, task_text)
                    page.snack_bar = ft.SnackBar(ft.Text(f"Completed: {task_text}"))
                    page.snack_bar.open = True
        render_tasks()

    def create_task_row(task_data):
        return ft.Row([
            ft.Checkbox(
                label=task_data["text"], 
                value=task_data["done"], 
                on_change=lambda e: toggle_task(task_data["text"], e.control.value)
            ),
            ft.IconButton(
                ft.Icons.DELETE_OUTLINE, 
                icon_color="red", 
                on_click=lambda e: delete_task(task_data["text"])
            )
        ], alignment="spaceBetween")

    view_tasks = ft.Column([
        ft.Text("My Tasks", size=30, weight="bold"),
        ft.Row([task_input, ft.IconButton(ft.Icons.ADD_CIRCLE, icon_color="green", on_click=add_task)]),
        ft.Divider(),
        tasks_view
    ], scroll="adaptive")

    # ==========================================
    # VIEW 3: WHEEL
    # ==========================================
    wheel_display = ft.Text("?", size=40, weight="bold", color=ft.Colors.CYAN_200, text_align="center")
    wheel_btn = ft.FilledButton("SPIN!", style=ft.ButtonStyle(bgcolor=ft.Colors.PINK_600, color="white"))

    async def spin_wheel(e):
        tasks = [t["text"] for t in APP_DATA["tasks"] if not t["done"]]
        if not tasks: 
            wheel_display.value = "Add tasks first!"
            page.update()
            return

        wheel_btn.disabled = True
        page.update()

        for _ in range(20):
            wheel_display.value = random.choice(tasks)
            wheel_display.color = random.choice([ft.Colors.CYAN_200, ft.Colors.YELLOW_200, ft.Colors.PURPLE_200])
            page.update()
            await asyncio.sleep(0.1)

        winner = random.choice(tasks)
        wheel_display.value = f"Selected:\n{winner}"
        wheel_display.color = ft.Colors.GREEN_400
        wheel_btn.disabled = False
        page.update()

    wheel_btn.on_click = spin_wheel

    view_wheel = ft.Column([
        ft.Text("Task Roulette", size=30, weight="bold"),
        ft.Container(height=50),
        ft.Container(
            content=wheel_display,
            padding=20,
            border=ft.Border.all(2, ft.Colors.GREY_800),
            border_radius=15,
            alignment=ft.Alignment(0, 0)
        ),
        ft.Container(height=30),
        wheel_btn
    ], horizontal_alignment="center", scroll="adaptive")

    # ==========================================
    # VIEW 4: LEADERBOARD
    # ==========================================
    lb_col = ft.Column(spacing=10)

    def get_lb_data():
        try:
            r = requests.get(FIREBASE_URL).json()
            if not r: return []
            user_stats = {}
            for v in r.values():
                name = v.get("username", "Unknown")
                dur_str = v.get("duration", "0 min")
                task_count = v.get("task_count", 0)
                try: mins = int(str(dur_str).split()[0])
                except: mins = 0
                if name not in user_stats: user_stats[name] = {"name": name, "total_minutes": 0, "total_tasks": 0}
                user_stats[name]["total_minutes"] += mins
                user_stats[name]["total_tasks"] += task_count

            final_list = []
            for name, stats in user_stats.items():
                total_m = stats["total_minutes"]
                h, m = divmod(total_m, 60)
                time_disp = f"{h}h {m}m" if h > 0 else f"{m} min"
                final_list.append({"name": name, "time": time_disp, "mins": total_m, "tasks": stats["total_tasks"]})
            return sorted(final_list, key=lambda x: x['mins'], reverse=True)
        except: return []

    def build_leaderboard(e=None):
        lb_col.controls.clear()
        data = get_lb_data()
        for i, u in enumerate(data):
            rank_color = ft.Colors.AMBER if i==0 else ft.Colors.WHITE
            card = ft.Container(
                padding=15, bgcolor="#0DFFFFFF", border_radius=15,
                content=ft.Row([
                    ft.Text(f"#{i+1}", size=20, weight="bold", color=rank_color, width=40),
                    ft.Column([ft.Text(u['name'], weight="bold"), ft.Text(f"{u['tasks']} tasks", size=12, color="grey")], expand=True),
                    ft.Text(u['time'], color="green", weight="bold"),
                ])
            )
            lb_col.controls.append(card)
        page.update()

    view_leaderboard = ft.Column([
        ft.Row([ft.Text("Leaderboard", size=30, weight="bold"), ft.FilledButton("Refresh", on_click=build_leaderboard)], alignment="spaceBetween"),
        lb_col
    ], scroll="adaptive")

    # ==========================================
    # MAIN NAVIGATION & LAYOUT
    # ==========================================
    username_input = ft.TextField(label="Your Username", value=APP_DATA["username"], on_blur=set_username)
    
    # We use a Container to switch views (Manual routing)
    body_container = ft.Container(content=view_leaderboard, expand=True, padding=10)

    def nav_change(e):
        idx = e.control.selected_index
        if idx == 0:
            body_container.content = view_timer
        elif idx == 1:
            body_container.content = view_tasks
            render_tasks()
        elif idx == 2:
            body_container.content = view_wheel
        elif idx == 3:
            body_container.content = view_leaderboard
            build_leaderboard()
        page.update()

    # 🟢 FIXED: Using NavigationBarDestination for Flet 0.80+
    page.navigation_bar = ft.NavigationBar(
        selected_index=3,
        on_change=nav_change,
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.TIMER, label="Timer"),
            ft.NavigationBarDestination(icon=ft.Icons.LIST, label="Tasks"),
            ft.NavigationBarDestination(icon=ft.Icons.CASINO, label="Wheel"),
            ft.NavigationBarDestination(icon=ft.Icons.LEADERBOARD, label="Ranks"),
        ]
    )

    page.add(
        ft.Row([username_input], alignment="center"),
        ft.Divider(),
        body_container
    )
    
    # Initialize
    render_tasks()
    build_leaderboard()

if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8550, host="0.0.0.0")