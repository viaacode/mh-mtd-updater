-- public.mh_mtd_cleanup definition

-- Drop table

-- DROP TABLE public.mh_mtd_cleanup;

CREATE TABLE public.mh_mtd_cleanup (
	fragment_id varchar(96) NOT NULL, -- The fragment_id of this item in MediaHaven.
	original_metadata xml NULL, -- Full metadata of the item in MediaHaven before transformation/update.
	transformed_metadata xml NULL, -- Metadata after transformation and cleaning: this is the new item's sidecar.
	transformations json NULL, -- JSON-representation of possible per-record transformations/updates.
	status TEXT NOT NULL CHECK (status IN ('TODO', 'IN_PROGRESS', 'DONE', 'ERROR')) DEFAULT ('TODO'),
	error text NULL,
	created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
	modified_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
	CONSTRAINT fragment_id_pkey PRIMARY KEY (fragment_id)
);
COMMENT ON TABLE public.mh_mtd_cleanup IS 'Table to hold all records for items who''s metadata needs to be rectified.';

-- Column comments

COMMENT ON COLUMN public.mh_mtd_cleanup.fragment_id IS 'The fragment_id of this item in MediaHaven.';
COMMENT ON COLUMN public.mh_mtd_cleanup.original_metadata IS 'Full metadata of the item in MediaHaven before transformation/update.';
COMMENT ON COLUMN public.mh_mtd_cleanup.transformed_metadata IS 'Metadata after transformation and cleaning: this is the new item''s sidecar.';
COMMENT ON COLUMN public.mh_mtd_cleanup.transformations IS 'JSON-representation of possible per-record transformations/updates.';

-- Table Triggers

CREATE TRIGGER sync_lastmod_mh_mtd_cleanup BEFORE
UPDATE
    ON
    public.mh_mtd_cleanup FOR EACH ROW EXECUTE FUNCTION sync_lastmod_mh_mtd_cleanup();

-- Permissions

ALTER TABLE public.mh_mtd_cleanup OWNER TO mh_migration;
GRANT ALL ON TABLE public.mh_mtd_cleanup TO mh_migration;
GRANT SELECT ON TABLE public.mh_mtd_cleanup TO superset_readonly_user;
