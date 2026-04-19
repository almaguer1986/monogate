"""
S77 — Challenge Board Update

Updates the challenge board:
  - sin(x) and cos(x): already closed (CLOSED) from earlier sessions
  - T19 (strict grammar): NEW ENTRY — CLOSED (proved)
  - T_i (extended grammar): remains OPEN

Challenge board is in Supabase. Uses the @supabase/supabase-js client
from the challenge directory.
"""

import json
import subprocess
import sys
from pathlib import Path

UPDATES = [
    {
        "id": "i-strict",
        "name": "i-Constructibility (Strict Grammar)",
        "description": (
            "Under strict principal-branch EML grammar (ln defined only on ℝ⁺, terminal {1}), "
            "prove or disprove that i = √(−1) is constructible."
        ),
        "status": "closed",
        "solution_session": "S70",
        "solution_summary": (
            "T19 (proved): 3-line induction. Strict grammar types all values as ℝ. "
            "Since i ∉ ℝ, i is not constructible. Lean verified in S74 (0 sorries)."
        ),
    },
]

# The T_i (extended grammar) challenge stays OPEN — no update needed.

UPDATE_SCRIPT = """
const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL,
  process.env.SUPABASE_SERVICE_ROLE_KEY
);

async function main() {
  const updates = JSON.parse(process.argv[2]);
  for (const update of updates) {
    console.log(`Updating: ${update.id} -> ${update.status}`);
    const { error } = await supabase
      .from('challenges')
      .update({
        status: update.status,
        solution_summary: update.solution_summary,
      })
      .eq('challenge_id', update.id);
    if (error) {
      console.error('Error:', error.message);
    } else {
      console.log('Updated:', update.id);
    }
  }
}

main().catch(console.error);
"""


def run_update():
    """Run the Supabase update from the challenge directory."""
    challenge_dir = Path("D:/monogate/challenge")
    if not challenge_dir.exists():
        return {"success": False, "error": "challenge dir not found"}

    script_path = challenge_dir / "_s77_update.js"
    try:
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(UPDATE_SCRIPT)

        result = subprocess.run(
            ["node", str(script_path), json.dumps(UPDATES)],
            cwd=str(challenge_dir),
            capture_output=True, text=True, encoding="utf-8", timeout=30
        )
        script_path.unlink(missing_ok=True)

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }
    except Exception as e:
        if script_path.exists():
            script_path.unlink(missing_ok=True)
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    results_dir = Path(__file__).parent.parent / "results"
    results_dir.mkdir(exist_ok=True)

    print("=" * 60)
    print("S77 — Challenge Board Update")
    print("=" * 60)
    print()
    print("Updates:")
    for u in UPDATES:
        print(f"  {u['id']}: {u['status'].upper()}")
        print(f"    {u['solution_summary'][:80]}...")
    print()

    result = run_update()
    print(f"Supabase update: {'SUCCESS' if result['success'] else 'FAILED'}")
    if result.get("stdout"):
        print(f"  {result['stdout']}")
    if result.get("stderr") and not result["success"]:
        print(f"  Error: {result['stderr'][:200]}")

    output = {
        "session": "S77",
        "updates": UPDATES,
        "result": result,
        "note": "T_i (extended grammar) remains OPEN on challenge board.",
    }

    out_path = results_dir / "s77_challenge_board.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    print(f"Results: {out_path}")
