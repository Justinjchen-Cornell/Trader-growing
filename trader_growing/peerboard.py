# -*- coding: utf-8 -*-
"""匿名同行榜（隐私优先设计）

- 无服务器：所有数据存本地，分享靠"导出成绩单 JSON"
- 匿名 ID：本地生成 uuid 短码，不包含任何个人信息
- 默认关闭：只有你主动导出/导入时才有同行数据
- 可以随时删除 peers/ 目录，不留痕迹
"""
import json, os, uuid, glob


def _data_dir():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "peers")


def _peers_dir():
    d = _data_dir()
    os.makedirs(d, exist_ok=True)
    return d


def _id_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "peer_id.txt")


def get_self_id():
    """读取或生成匿名 ID（本地）"""
    p = _id_path()
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return f.read().strip()
    pid = uuid.uuid4().hex[:8]
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(pid)
    return pid


class PeerBoard:
    def __init__(self):
        self.self_id = get_self_id()
        self.peers_dir = _peers_dir()

    # ---- 导出自己的匿名成绩单 ----
    def export_card(self, char, ach, best, tier_name):
        s = char.summary()
        try:
            from trader_growing.levels import Progress
            prog = Progress()
            levels_done = len(prog.completed)
            worlds_done = prog.worlds_cleared()
        except Exception:
            levels_done, worlds_done = 0, 0
        return {
            "id": self.self_id,
            "level": s["level"],
            "xp": s["xp"],
            "streak": s["streak"],
            "total_days": s["total_days"],
            "dims": s["dims"],
            "badges": len(ach.summary()),
            "bestiary": len(best.unlocked),
            "levels": levels_done,
            "worlds": worlds_done,
            "tier": tier_name,
            "exported_at": __import__("datetime").date.today().isoformat(),
            "note": "Trader-growing 匿名成绩单，不含任何个人信息",
        }

    def save_own_card(self, card):
        with open(os.path.join(self.peers_dir, "self_" + self.self_id + ".json"), "w", encoding="utf-8") as f:
            json.dump(card, f, ensure_ascii=False, indent=2)

    def import_card(self, path):
        """导入他人成绩单，返回 (card, error)"""
        try:
            with open(path, encoding="utf-8") as f:
                card = json.load(f)
            if card.get("id") == self.self_id:
                return None, "这是你自己的卡片"
            if not card.get("xp"):
                return None, "无效卡片"
            dst = os.path.join(self.peers_dir, "peer_" + card["id"] + ".json")
            with open(dst, "w", encoding="utf-8") as f:
                json.dump(card, f, ensure_ascii=False, indent=2)
            return card, None
        except (json.JSONDecodeError, OSError) as e:
            return None, "读取失败: {}".format(e)

    def import_card_data(self, data, filename=None):
        """从上传的数据导入（Streamlit 用）"""
        import io
        try:
            card = json.loads(data.decode("utf-8"))
            if card.get("id") == self.self_id:
                return None, "这是你自己的卡片"
            if not card.get("xp"):
                return None, "无效卡片"
            dst = os.path.join(self.peers_dir, "peer_" + card["id"] + ".json")
            with open(dst, "w", encoding="utf-8") as f:
                json.dump(card, f, ensure_ascii=False, indent=2)
            return card, None
        except (json.JSONDecodeError, ValueError) as e:
            return None, "解析失败: {}".format(e)

    def remove_peer(self, pid):
        p = os.path.join(self.peers_dir, "peer_" + pid + ".json")
        if os.path.exists(p):
            os.remove(p)
            return True
        return False

    def leaderboard(self, own_card):
        """本地排名：自己 + 已导入的同行，按 XP 排序"""
        rows = []
        if own_card:
            rows.append(own_card)
        for fp in sorted(glob.glob(os.path.join(self.peers_dir, "peer_*.json"))):
            try:
                with open(fp, encoding="utf-8") as f:
                    rows.append(json.load(f))
            except (json.JSONDecodeError, OSError):
                continue
        rows.sort(key=lambda c: c.get("xp", 0), reverse=True)
        for i, r in enumerate(rows, 1):
            r["rank"] = i
        return rows
