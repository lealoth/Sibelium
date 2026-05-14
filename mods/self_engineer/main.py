"""Self Engineer Mod - setup/teardown."""
import json
from pathlib import Path
from datetime import datetime
from mods.self_engineer.code_reader import CodeReader
from mods.self_engineer.self_engineer import SelfEngineer
from mods.self_engineer.code_executor import CodeExecutor


def setup(flow_manager):
    base_dir = Path(__file__).resolve().parent.parent.parent
    engineer = SelfEngineer(flow_manager, base_dir)
    executor = CodeExecutor()
    
    flow_manager.code_reader = engineer.reader
    flow_manager.self_engineer = engineer
    flow_manager.code_executor = executor
    
    last_run = {"time": None}
    
    mod_json = Path(__file__).parent / "mod.json"
    config = {}
    if mod_json.exists():
        metadata = json.loads(mod_json.read_text(encoding="utf-8"))
        config = metadata.get("config", {})
    
    interval_hours = config.get("analysis_interval_hours", 24)
    if interval_hours == 0:
        interval_seconds = 0
    else:
        interval_seconds = int(interval_hours * 3600)
    
    def on_startup(fm):
        engineer.reader.index_codebase()
        print("   [SelfEngineer] Codebase indexed.")
        if interval_seconds == 0:
            try:
                engineer.run_cycle()
            except Exception as e:
                print(f"   [!] Error en ciclo inicial: {e}")
    
    def on_slow_tick(fm):
        nonlocal last_run
        now = datetime.now()
        if interval_seconds > 0 and last_run["time"] and (now - last_run["time"]).total_seconds() < interval_seconds:
            return
        last_run["time"] = now
        try:
            result = engineer.run_cycle()
            if result and hasattr(fm, '_team_channel') and fm._team_channel:
                proposals = engineer.get_proposals()
                if proposals:
                    latest = proposals[-1]
                    fm._team_channel.send(
                        sender="Ada",
                        receiver="Nexus",
                        message=f"Análisis de {latest['file']}:\n{latest['analysis'][:500]}",
                        msg_type="code_review"
                    )
                    print(f"   [SelfEngineer] Propuesta enviada a Nexus.")
            
            if hasattr(fm, '_team_channel') and fm._team_channel:
                replies = fm._team_channel.check("Ada")
                for reply in replies:
                    if reply.get("type") == "review":
                        from core.flow.flow_stream import ThoughtItem
                        fm.stream.add_thought(ThoughtItem(
                            content=f"[Feedback de {reply['sender']}] {reply['message'][:200]}",
                            thought_type="feedback",
                            priority=0.7,
                            source="team_channel"
                        ))
                        print(f"   [SelfEngineer] Feedback recibido de {reply['sender']}.")

        except Exception as e:
            print(f"   [!] Error en ciclo de automejora: {e}")
    
    flow_manager._mod_hooks["on_startup"].append(on_startup)
    flow_manager._mod_hooks["on_slow_tick"].append(on_slow_tick)
    
    print("   [SelfEngineer] Ready.")
    return {"engineer": engineer, "executor": executor}


def teardown(flow_manager):
    flow_manager.code_reader = None
    flow_manager.self_engineer = None
    flow_manager.code_executor = None
    print("   [SelfEngineer] Disabled.")