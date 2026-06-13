import json
from pathlib import Path
from typing import Any


class MitreData:
    def __init__(self, data_dir: str | Path | None = None):
        if data_dir is None:
            data_dir = Path(__file__).parent.parent.parent

        self.data_dir = Path(data_dir)
        self._attack_data: dict[str, Any] | None = None
        self._defend_data: dict[str, Any] | None = None
        self._attack_techniques: dict[str, dict[str, Any]] | None = None
        self._defend_techniques: dict[str, dict[str, Any]] | None = None

    @property
    def attack_data(self) -> dict[str, Any]:
        if self._attack_data is None:
            attack_path = self.data_dir / "enterprise-attack.json"
            if not attack_path.exists():
                raise FileNotFoundError(
                    f"ATT&CK data not found at {attack_path}. "
                    "Run: python scripts/download_mitre_data.py"
                )
            with open(attack_path) as f:
                self._attack_data = json.load(f)
        return self._attack_data

    @property
    def defend_data(self) -> dict[str, Any]:
        if self._defend_data is None:
            defend_path = self.data_dir / "d3fend.json"
            if not defend_path.exists():
                raise FileNotFoundError(
                    f"D3FEND data not found at {defend_path}. "
                    "Run: python scripts/download_mitre_data.py"
                )
            with open(defend_path) as f:
                self._defend_data = json.load(f)
        return self._defend_data

    def _build_attack_index(self) -> dict[str, dict[str, Any]]:
        if self._attack_techniques is not None:
            return self._attack_techniques

        self._attack_techniques = {}
        for obj in self.attack_data.get("objects", []):
            if obj.get("type") != "attack-pattern":
                continue
            if obj.get("revoked", False):
                continue

            technique_id = None
            url = None
            for ref in obj.get("external_references", []):
                if ref.get("source_name") == "mitre-attack":
                    technique_id = ref.get("external_id")
                    url = ref.get("url")
                    break

            if technique_id:
                tactics = []
                for phase in obj.get("kill_chain_phases", []):
                    if phase.get("kill_chain_name") == "mitre-attack":
                        tactics.append(phase["phase_name"])

                self._attack_techniques[technique_id] = {
                    "id": technique_id,
                    "name": obj.get("name"),
                    "description": obj.get("description", ""),
                    "tactics": tactics,
                    "url": url,
                    "platforms": obj.get("x_mitre_platforms", []),
                    "detection": obj.get("x_mitre_detection", ""),
                }

        return self._attack_techniques

    def _build_defend_index(self) -> dict[str, dict[str, Any]]:
        if self._defend_techniques is not None:
            return self._defend_techniques

        self._defend_techniques = {}
        for item in self.defend_data.get("@graph", []):
            d3f_id = item.get("d3f:d3fend-id")
            if not d3f_id or not d3f_id.startswith("D3-"):
                continue

            tactic = self._get_defend_tactic_from_ontology(item)

            self._defend_techniques[d3f_id] = {
                "id": d3f_id,
                "name": item.get("rdfs:label", ""),
                "definition": item.get("d3f:definition", ""),
                "tactic": tactic,
                "url": f"https://d3fend.mitre.org/technique/d3f:{item.get('@id', '').replace('d3f:', '')}",
            }

        return self._defend_techniques

    def _get_defend_tactic_from_ontology(self, item: dict) -> str | None:
        tactic_ids = {
            "d3f:Model": "Model",
            "d3f:Harden": "Harden",
            "d3f:Detect": "Detect",
            "d3f:Isolate": "Isolate",
            "d3f:Deceive": "Deceive",
            "d3f:Evict": "Evict",
            "d3f:Restore": "Restore",
        }

        if not hasattr(self, "_defend_items_by_id"):
            self._defend_items_by_id = {
                i.get("@id", ""): i for i in self.defend_data.get("@graph", [])
            }

        def find_tactic(current_item, visited=None):
            if visited is None:
                visited = set()

            item_id = current_item.get("@id", "")
            if item_id in visited:
                return None
            visited.add(item_id)

            enables = current_item.get("d3f:enables", {})
            if isinstance(enables, dict):
                tactic_id = enables.get("@id", "")
                if tactic_id in tactic_ids:
                    return tactic_ids[tactic_id]

            subclass = current_item.get("rdfs:subClassOf", [])
            if isinstance(subclass, dict):
                subclass = [subclass]

            for sc in subclass:
                if isinstance(sc, dict) and "@id" in sc:
                    parent_id = sc["@id"]
                    parent = self._defend_items_by_id.get(parent_id)
                    if parent:
                        result = find_tactic(parent, visited)
                        if result:
                            return result

            return None

        return find_tactic(item)

    def get_attack_technique(self, technique_id: str) -> dict[str, Any] | None:
        index = self._build_attack_index()
        return index.get(technique_id)

    def get_defend_technique(self, technique_id: str) -> dict[str, Any] | None:
        index = self._build_defend_index()
        return index.get(technique_id)

    def search_attack_techniques(self, query: str) -> list[dict[str, Any]]:
        index = self._build_attack_index()
        query_lower = query.lower()
        results = []
        for technique in index.values():
            if (
                query_lower in technique["name"].lower()
                or query_lower in technique.get("description", "").lower()
            ):
                results.append(technique)
        return results

    def search_defend_techniques(self, query: str) -> list[dict[str, Any]]:
        index = self._build_defend_index()
        query_lower = query.lower()
        results = []
        for technique in index.values():
            if (
                query_lower in technique["name"].lower()
                or query_lower in technique.get("definition", "").lower()
            ):
                results.append(technique)
        return results

    def get_all_attack_techniques(self) -> list[dict[str, Any]]:
        return list(self._build_attack_index().values())

    def get_all_defend_techniques(self) -> list[dict[str, Any]]:
        return list(self._build_defend_index().values())

    def validate_attack_mapping(self, technique_id: str) -> bool:
        return self.get_attack_technique(technique_id) is not None

    def validate_defend_mapping(self, technique_id: str) -> bool:
        return self.get_defend_technique(technique_id) is not None

    def get_defend_tactic(self, technique_id: str) -> str | None:
        for tactic, tech_ids in DEFEND_TACTICS.items():
            if technique_id in tech_ids:
                return tactic
        return None

    def get_techniques_by_defend_tactic(self, tactic: str) -> list[str]:
        return DEFEND_TACTICS.get(tactic, [])


ATTACK_TACTICS = {
    "TA0043": "reconnaissance",
    "TA0042": "resource-development",
    "TA0001": "initial-access",
    "TA0002": "execution",
    "TA0003": "persistence",
    "TA0004": "privilege-escalation",
    "TA0005": "defense-evasion",
    "TA0006": "credential-access",
    "TA0007": "discovery",
    "TA0008": "lateral-movement",
    "TA0009": "collection",
    "TA0011": "command-and-control",
    "TA0010": "exfiltration",
    "TA0040": "impact",
}

ATTACK_TACTIC_IDS = {v: k for k, v in ATTACK_TACTICS.items()}


DEFEND_TACTICS = {
    "Model": [
        "D3-AI",
        "D3-AVE",
        "D3-CIA",
        "D3-CI",
        "D3-SWI",
        "D3-NVA",
        "D3-SYSVA",
        "D3-PLM",
        "D3-LLM",
        "D3-ALLM",
        "D3-PLLM",
        "D3-ODM",
        "D3-AM",
    ],
    "Harden": [
        "D3-MFA",
        "D3-BAN",
        "D3-CBAN",
        "D3-ACH",
        "D3-CH",
        "D3-CP",
        "D3-CRO",
        "D3-CERO",
        "D3-SU",
        "D3-BA",
        "D3-FE",
        "D3-DE",
    ],
    "Detect": [
        "D3-NTA",
        "D3-NTSA",
        "D3-FA",
        "D3-FCA",
        "D3-PM",
        "D3-FIM",
        "D3-LAM",
        "D3-DAM",
        "D3-ANET",
        "D3-AZET",
        "D3-RTSD",
        "D3-PSA",
        "D3-PSMD",
        "D3-CCSA",
        "D3-UGLPA",
    ],
    "Isolate": [
        "D3-NTF",
        "D3-ITF",
        "D3-OTF",
        "D3-EF",
        "D3-NI",
        "D3-BDI",
        "D3-ET",
        "D3-EAL",
        "D3-EDL",
        "D3-SCF",
        "D3-CF",
        "D3-CQ",
        "D3-UAP",
    ],
    "Deceive": ["D3-DE", "D3-CHN", "D3-DNR", "D3-DF", "D3-DP", "D3-DST", "D3-DUC"],
    "Evict": ["D3-CE", "D3-AL", "D3-ANCI", "D3-CR", "D3-FE", "D3-PT", "D3-PS", "D3-HR", "D3-HS"],
    "Restore": ["D3-RC", "D3-RCO", "D3-RDB", "D3-RDI", "D3-RF", "D3-RS", "D3-UA"],
}

DEFEND_TACTIC_DESCRIPTIONS = {
    "Model": "Gather information about systems, assets, and configurations",
    "Harden": "Increase the difficulty of exploiting a system",
    "Detect": "Identify potentially malicious activity",
    "Isolate": "Create logical or physical barriers to limit access",
    "Deceive": "Mislead adversaries with false information or decoys",
    "Evict": "Remove adversary presence from systems",
    "Restore": "Return systems to a known good state",
}
