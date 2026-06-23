-- This script belongs to Phase 001 and must not be executed in Phase 000.
ALTER TABLE databricks_arrow_cata.bronz.sales_info
SET TBLPROPERTIES (delta.enableChangeDataFeed = true);
