#!/usr/bin/env python
"""AI usage & cost dashboard summary (production ops)."""
import os
import sys
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

import django

django.setup()

from django.db.models import Count, Sum
from user_sessions.models import AIUsageLog


def main():
    qs = AIUsageLog.objects.all()
    total = qs.count()
    if total == 0:
        print("No AIUsageLog rows yet. Run RAG queries with AI_USAGE_LOGGING=true.")
        return

    agg = qs.aggregate(
        total_cost=Sum("estimated_cost_usd"),
        prompt=Sum("prompt_tokens"),
        completion=Sum("completion_tokens"),
        embedding=Sum("embedding_tokens"),
        total_tokens=Sum("total_tokens"),
    )
    cache_hits = qs.filter(cache_hit=True).count()

    print("=" * 60)
    print("AI Usage Report")
    print("=" * 60)
    print(f"Total requests:     {total}")
    print(f"Cache hits:         {cache_hits} ({100*cache_hits/total:.1f}%)")
    print(f"Total tokens:       {agg['total_tokens'] or 0}")
    print(f"  prompt:           {agg['prompt'] or 0}")
    print(f"  completion:       {agg['completion'] or 0}")
    print(f"  embedding:        {agg['embedding'] or 0}")
    print(f"Est. total cost:    ${agg['total_cost'] or Decimal('0')}")
    print()
    print("By agent:")
    for row in qs.values("agent_id").annotate(
        n=Count("id"), cost=Sum("estimated_cost_usd"), tok=Sum("total_tokens")
    ).order_by("-cost")[:10]:
        print(f"  {row['agent_id']:20} {row['n']:5} req  ${row['cost'] or 0:.4f}  {row['tok'] or 0} tok")
    print()
    print("Top users by cost:")
    for row in qs.filter(user__isnull=False).values("user__email").annotate(
        n=Count("id"), cost=Sum("estimated_cost_usd")
    ).order_by("-cost")[:5]:
        print(f"  {row['user__email'] or 'anon':30} ${row['cost'] or 0:.4f}")


if __name__ == "__main__":
    main()
