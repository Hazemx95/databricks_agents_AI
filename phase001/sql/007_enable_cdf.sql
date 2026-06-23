-- Phase 001 only. This file is intentionally outside the Phase 000 sql/ path.
ALTER TABLE databricks_arrow_cata.bronz.sales_info
SET TBLPROPERTIES (delta.enableChangeDataFeed = true);
