from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Tuple, Iterable

# v1 assumptions (you can override via CLI flags)
DEFAULT_GB_MONTH = 0.08   # USD per GB-month for unattached EBS (assume gp3)
DEFAULT_EIP_HOURLY = 0.005  # USD per hour for idle EIP (~$3.60/mo at 720h)

@dataclass
class StoppedInstance:
    instance_id: str
    name: str

@dataclass
class UnattachedVolume:
    volume_id: str
    vol_type: str
    size_gb: int

@dataclass
class UnusedEip:
    allocation_id: str
    public_ip: str

@dataclass
class MissingTag:
    resource_type: str
    resource_id: str
    missing: List[str]

def _get_name_tag(tags: Iterable[Dict]) -> str:
    for t in tags or []:
        if t.get("Key") == "Name" and t.get("Value"):
            return t["Value"]
    return ""

def list_stopped_instances(ec2) -> List[StoppedInstance]:
    """All stopped EC2 instances (simple v1: no age filter)."""
    out: List[StoppedInstance] = []
    paginator = ec2.get_paginator("describe_instances")
    for page in paginator.paginate(
        Filters=[{"Name": "instance-state-name", "Values": ["stopped"]}]
    ):
        for r in page.get("Reservations", []):
            for i in r.get("Instances", []):
                out.append(
                    StoppedInstance(
                        instance_id=i["InstanceId"],
                        name=_get_name_tag(i.get("Tags"))
                    )
                )
    return out

def list_unattached_volumes(ec2) -> List[UnattachedVolume]:
    """EBS volumes in 'available' (not attached)."""
    out: List[UnattachedVolume] = []
    paginator = ec2.get_paginator("describe_volumes")
    for page in paginator.paginate(
        Filters=[{"Name": "status", "Values": ["available"]}]
    ):
        for v in page.get("Volumes", []):
            out.append(
                UnattachedVolume(
                    volume_id=v["VolumeId"],
                    vol_type=v.get("VolumeType", "gp3"),
                    size_gb=int(v.get("Size", 0)),
                )
            )
    return out

def list_unused_eips(ec2) -> List[UnusedEip]:
    """Elastic IPs without an association."""
    out: List[UnusedEip] = []
    paginator = ec2.get_paginator("describe_addresses")
    for page in paginator.paginate():
        for a in page.get("Addresses", []):
            # Unassociated if there's no AssociationId
            if not a.get("AssociationId"):
                out.append(
                    UnusedEip(
                        allocation_id=a.get("AllocationId", ""),
                        public_ip=a.get("PublicIp", ""),
                    )
                )
    return out

def list_untagged_resources(ec2, required_tags: List[str]) -> List[MissingTag]:
    """Check Instances + Volumes for missing required tags."""
    missing: List[MissingTag] = []

    # Instances
    paginator = ec2.get_paginator("describe_instances")
    for page in paginator.paginate():
        for r in page.get("Reservations", []):
            for inst in r.get("Instances", []):
                tags = inst.get("Tags") or []
                have = {t["Key"] for t in tags if "Key" in t}
                need = [t for t in required_tags if t not in have]
                if need:
                    missing.append(MissingTag("ec2:instance", inst["InstanceId"], need))

    # Volumes
    paginator = ec2.get_paginator("describe_volumes")
    for page in paginator.paginate():
        for vol in page.get("Volumes", []):
            tags = vol.get("Tags") or []
            have = {t["Key"] for t in tags if "Key" in t}
            need = [t for t in required_tags if t not in have]
            if need:
                missing.append(MissingTag("ec2:volume", vol["VolumeId"], need))

    # (EIPs may or may not have tags; skipping in v1 to keep it simple)
    return missing

def estimate_monthly_waste(
    volumes: List[UnattachedVolume],
    eips: List[UnusedEip],
    gb_month_rate: float,
    eip_hour_rate: float,
) -> Tuple[float, float]:
    """Return (volumes_cost, eips_cost) using simple assumptions."""
    vols_cost = sum(v.size_gb * gb_month_rate for v in volumes)
    eips_cost = len(eips) * eip_hour_rate * 720  # ~hours/month
    return vols_cost, eips_cost

# ---------- rendering (plain text for now) ----------

def _print_header(title: str):
    print("\n" + title)
    print("-" * len(title))

def _print_table(headers: List[str], rows: List[List[str]]):
    print("  " + " | ".join(headers))
    print("  " + "-+-".join("-" * len(h) for h in headers))
    for r in rows:
        print("  " + " | ".join(r))

def run_audit(session, profile: str | None, region: str | None,
              required_tags_csv: str,
              gb_month_rate: float,
              eip_hour_rate: float):
    ec2 = session.client("ec2")

    # 1) Stopped instances
    stopped = list_stopped_instances(ec2)
    _print_header("Stopped EC2 instances (potential waste)")
    if stopped:
        rows = [[s.instance_id, s.name or "-"] for s in stopped]
        _print_table(["InstanceId", "Name"], rows)
        print(f"  Total: {len(stopped)}")
    else:
        print("  None found.")

    # 2) Unattached EBS
    unattached = list_unattached_volumes(ec2)
    _print_header("Unattached EBS volumes")
    if unattached:
        rows = [[u.volume_id, u.vol_type, f"{u.size_gb} GB"] for u in unattached]
        _print_table(["VolumeId", "Type", "Size"], rows)
        print(f"  Total: {len(unattached)}")
    else:
        print("  None found.")

    # 3) Unused EIPs
    unused = list_unused_eips(ec2)
    _print_header("Unused Elastic IPs (unassociated)")
    if unused:
        rows = [[u.allocation_id or "-", u.public_ip or "-"] for u in unused]
        _print_table(["AllocationId", "PublicIp"], rows)
        print(f"  Total: {len(unused)}")
    else:
        print("  None found.")

    # 4) Untagged resources
    required = [s.strip() for s in (required_tags_csv or "").split(",") if s.strip()]
    if required:
        missing = list_untagged_resources(ec2, required)
        _print_header(f"Untagged resources (required: {', '.join(required)})")
        if missing:
            rows = [[m.resource_type, m.resource_id, ", ".join(m.missing)] for m in missing[:50]]
            _print_table(["Resource", "Id", "Missing tags"], rows)
            more = max(0, len(missing) - 50)
            if more:
                print(f"  ...and {more} more")
            print(f"  Total missing: {len(missing)}")
        else:
            print("  None missing required tags.")

    # 5) Simple estimated monthly waste
    vols_cost, eips_cost = estimate_monthly_waste(unattached, unused, gb_month_rate, eip_hour_rate)
    _print_header("Estimated monthly waste (simple assumptions)")
    print(f"  Unattached EBS: ~${vols_cost:,.2f} (assumes ${gb_month_rate:.3f}/GB-month)")
    print(f"  Unused EIPs   : ~${eips_cost:,.2f} (assumes ${eip_hour_rate:.3f}/hour × 720h)")
    print("\nNotes:")
    print("  • These are rough estimates; confirm with AWS pricing for your region.")
    print("  • Use CLI flags to override assumptions (see --help).")
