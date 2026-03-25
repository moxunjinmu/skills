# Feishu Bitable Workflow

## Rule

If a Bitable belongs to a knowledge system, create it inside the knowledge base/wiki structure first.
Do not treat an independent Base app as the formal destination unless explicitly intended.

## Recommended Order

1. Confirm destination knowledge space and parent node
2. Create the Bitable under the correct wiki node
3. Clean default blank rows and default placeholder fields
4. Add custom fields
5. Write real records
6. Verify the final table URL is the knowledge-base table, not an orphan Base app

## Cleanup Rule

New Bitables often contain:
- 10 blank rows
- default placeholder columns

These should be removed before considering the table finished.

## Data Placement Rule

- Structural rule / location decision → `MEMORY.md`
- Exact app_token / table_id / URL → `TOOLS.md`
- Task-day process detail → `memory/YYYY-MM-DD.md`

## Current Known Formal Tables

### 内容获客库 → 08-内容资产
- 网站参考案例库: `Jr5ubwVukaGI5esV3wwcxFIindf` / `tblG4sigGcbjtgF2`
- 风格提示词库: `S58sb2Q3qamJFBsMwyrcjnnLnRh` / `tblTfEt2fCubGPb7`

## Known Gotcha

Independent Base apps can look correct but still not be the real wiki-hosted table. Always verify final app/table identity.
