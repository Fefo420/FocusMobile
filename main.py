import flet as ft
import requests

def main(page: ft.Page):
    # App Configuration
    page.title = "Focus Leaderboard"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.scroll = "adaptive"  
    
    # Your Firebase URL
    FIREBASE_URL = "https://productivity-71d06-default-rtdb.europe-west1.firebasedatabase.app/leaderboard.json"

    # --- Data Fetching Logic (Now with Math!) ---
    def get_data():
        try:
            r = requests.get(FIREBASE_URL).json()
            if not r: return []
            
            # 1. Aggregate (Combine) the data by Username
            user_stats = {}
            
            for v in r.values():
                name = v.get("username", "Unknown")
                dur_str = v.get("duration", "0 min")
                task_count = v.get("task_count", 0)
                
                # Extract number of minutes
                try: mins = int(str(dur_str).split()[0])
                except: mins = 0
                
                # Initialize user if new
                if name not in user_stats:
                    user_stats[name] = {
                        "name": name,
                        "total_minutes": 0,
                        "total_tasks": 0
                    }
                
                # Add to totals
                user_stats[name]["total_minutes"] += mins
                user_stats[name]["total_tasks"] += task_count

            # 2. Convert to List and Format
            final_list = []
            for name, stats in user_stats.items():
                total_m = stats["total_minutes"]
                
                # Format: "1h 30m" or "45 min"
                hours, minutes = divmod(total_m, 60)
                if hours > 0:
                    time_display = f"{hours}h {minutes}m"
                else:
                    time_display = f"{minutes} min"
                
                final_list.append({
                    "name": name,
                    "time": time_display,
                    "mins": total_m, # Used for sorting
                    "tasks": stats["total_tasks"]
                })

            # 3. Sort High to Low
            return sorted(final_list, key=lambda x: x['mins'], reverse=True)

        except Exception as e:
            print(f"Error: {e}")
            return []

    # --- UI Builder ---
    def build_leaderboard(e=None):
        data = get_data()
        
        # Clear existing controls
        list_column.controls.clear()
        
        if not data:
            list_column.controls.append(ft.Text("No data yet.", color="grey"))
            page.update()
            return

        for i, u in enumerate(data):
            # Rank Colors
            rank_color = ft.Colors.WHITE
            icon = ""
            if i == 0: 
                rank_color = ft.Colors.AMBER
                icon = "👑"
            elif i == 1: 
                rank_color = ft.Colors.GREY_400
            elif i == 2: 
                rank_color = ft.Colors.BROWN_400

            # Card UI
            card = ft.Container(
                padding=15,
                bgcolor="#0DFFFFFF", 
                border_radius=15,
                content=ft.Row([
                    ft.Text(f"{icon} #{i+1}", size=20, weight="bold", color=rank_color, width=60),
                    ft.Column([
                        ft.Text(u['name'], size=18, weight="bold"),
                        ft.Text(f"{u['tasks']} tasks completed", size=12, color=ft.Colors.GREY)
                    ], expand=True),
                    ft.Text(u['time'], color=ft.Colors.GREEN_400, weight="bold", size=16),
                ], alignment="spaceBetween")
            )
            list_column.controls.append(card)
        
        page.update()

    # --- Layout Setup ---
    list_column = ft.Column(spacing=10)
    
    # Header
    page.add(
        ft.Row([
            ft.Text("🏆 Leaderboard", size=24, weight="bold"),
            ft.ElevatedButton(
                "Refresh", 
                on_click=build_leaderboard, 
                bgcolor=ft.Colors.BLUE_GREY_900, 
                color="white"
            )
        ], alignment="spaceBetween"),
        ft.Divider(height=20, color="transparent"),
        list_column
    )

    # Load data on startup
    build_leaderboard()

# Run the app
if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8550, host="0.0.0.0")