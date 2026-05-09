# Deals Table Guide - Status and Queries

## Table Information

**Table Name**: `deals`

## Important: NO Traditional Status System!

❌ The `deals` table does **NOT** have a "pending", "active", "approved" status system
❌ `status_id` column exists but is ALL NULL (not used)
❌ `lifecycle_type` column exists but is ALL NULL (not used)
❌ There is NO `deal_statuses` table

## What EXISTS: Complete/Incomplete

The deals table uses a **simple binary system**:

- `complete` - **INTEGER: 0 = Incomplete/In-Progress, 1 = Complete/Finished**
- `completed_at` - Timestamp when deal was completed (NULL if not complete)
- `deleted_at` - Soft delete (NULL = active deal)

## Current Deal Statistics

- **Complete deals**: 507 (`complete = 1`)
- **Incomplete deals**: 449 (`complete = 0`)
- **Total active deals**: 956

## Common Queries

### Count All Active Deals
```sql
SELECT COUNT(*) as total FROM deals WHERE deleted_at IS NULL
```

### Count Complete Deals
```sql
SELECT COUNT(*) as total FROM deals WHERE complete = 1 AND deleted_at IS NULL
```

### Count Incomplete Deals
```sql
SELECT COUNT(*) as total FROM deals WHERE complete = 0 AND deleted_at IS NULL
```

### Count Deals Without Completion Date
```sql
SELECT COUNT(*) as total FROM deals WHERE completed_at IS NULL AND deleted_at IS NULL
```

## Query Patterns - What to Map

When user asks:
- "How many deals" → Query `deals` table (all active)
- "How many complete deals" → Query `deals` WHERE `complete = 1`
- "How many incomplete deals" → Query `deals` WHERE `complete = 0`
- "How many finished deals" → Query `deals` WHERE `complete = 1`
- "How many in-progress deals" → Query `deals` WHERE `complete = 0`
- "How many uncompleted deals" → Query `deals` WHERE `complete = 0`

## ❌ INVALID Queries (These Concepts DON'T EXIST)

- "How many pending deals" → **NO "pending" status exists**
- "How many approved deals" → **NO "approved" status exists**
- "How many active deals" → **Ambiguous** (could mean incomplete OR all non-deleted)
- "How many open deals" → **Ambiguous** (suggest incomplete instead)

## Important Notes

1. **Always check `deleted_at IS NULL`** for active records
2. **`complete = 0`** means deal is still in progress/incomplete
3. **`complete = 1`** means deal is finished/complete
4. If user asks for "pending", **suggest they mean "incomplete"** or ask for clarification
5. There are OTHER status fields like `lending_deal_statuses` but they're NOT connected to the main `deals` table

## Related Tables

- `deal_products` - Products associated with deals
- `deal_fees` - Fees for deals
- `deal_taxes` - Taxes for deals
- `lending_deal_statuses` - Separate lending status system (NOT linked to deals.status_id)

## Example Results

- **Total active deals**: 956
- **Complete deals**: 507  
- **Incomplete deals**: 449

