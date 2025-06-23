CREATE TABLE IF NOT EXISTS public.files
(
    id integer NOT NULL DEFAULT nextval('files_id_seq'::regclass),
    file_name character varying(100) COLLATE pg_catalog."default" NOT NULL,
    file_path character varying(200) COLLATE pg_catalog."default" NOT NULL,
    original_name character varying(100) COLLATE pg_catalog."default" NOT NULL,
    file_size bigint NOT NULL,
    is_public boolean DEFAULT true,
    discipline character varying(50) COLLATE pg_catalog."default" NOT NULL,
    dimension character varying(10) COLLATE pg_catalog."default" NOT NULL,
    file_type character varying(20) COLLATE pg_catalog."default" NOT NULL,
    coordinate_system character varying(20) COLLATE pg_catalog."default",
    tags character varying(200) COLLATE pg_catalog."default",
    description text COLLATE pg_catalog."default",
    user_id integer,
    upload_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    status character varying(20) COLLATE pg_catalog."default" DEFAULT 'uploaded'::character varying,
    bbox jsonb,
    geometry_type character varying(50) COLLATE pg_catalog."default",
    feature_count integer,
    metadata jsonb,
    CONSTRAINT files_pkey PRIMARY KEY (id),
    CONSTRAINT files_user_id_fkey FOREIGN KEY (user_id)
        REFERENCES public.users (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

CREATE TABLE IF NOT EXISTS public.scene_layers
(
    id integer NOT NULL DEFAULT nextval('scene_layers_id_seq'::regclass),
    scene_id integer,
    layer_id integer,
    layer_order integer DEFAULT 0,
    visible boolean DEFAULT true,
    opacity numeric(3,2) DEFAULT 1.0,
    style_name character varying(100) COLLATE pg_catalog."default",
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    custom_style jsonb,
    queryable boolean DEFAULT true,
    selectable boolean DEFAULT true,
    CONSTRAINT scene_layers_pkey PRIMARY KEY (id),
    CONSTRAINT scene_layers_scene_id_layer_id_key UNIQUE (scene_id, layer_id),
    CONSTRAINT scene_layers_layer_id_fkey FOREIGN KEY (layer_id)
        REFERENCES public.geoserver_layers (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE,
    CONSTRAINT scene_layers_scene_id_fkey FOREIGN KEY (scene_id)
        REFERENCES public.scenes (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)
CREATE TABLE IF NOT EXISTS public.scenes
(
    id integer NOT NULL DEFAULT nextval('scenes_id_seq'::regclass),
    name character varying(100) COLLATE pg_catalog."default" NOT NULL,
    description text COLLATE pg_catalog."default",
    is_public boolean DEFAULT true,
    user_id integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT scenes_pkey PRIMARY KEY (id),
    CONSTRAINT scenes_user_id_fkey FOREIGN KEY (user_id)
        REFERENCES public.users (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)
CREATE TABLE IF NOT EXISTS public.users
(
    id bigint NOT NULL,
    username character varying(50) COLLATE pg_catalog."default" NOT NULL,
    password character varying(100) COLLATE pg_catalog."default" NOT NULL,
    email character varying(100) COLLATE pg_catalog."default",
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT users_pkey PRIMARY KEY (id),
    CONSTRAINT users_username_key UNIQUE (username),
    CONSTRAINT users_email_key UNIQUE (email)
)
CREATE TABLE IF NOT EXISTS public.geoserver_coverages
(
    id integer NOT NULL DEFAULT nextval('geoserver_coverages_id_seq'::regclass),
    name character varying(100) COLLATE pg_catalog."default" NOT NULL,
    native_name character varying(100) COLLATE pg_catalog."default",
    store_id integer,
    title character varying(255) COLLATE pg_catalog."default",
    abstract text COLLATE pg_catalog."default",
    keywords text[] COLLATE pg_catalog."default",
    srs character varying(50) COLLATE pg_catalog."default" DEFAULT 'EPSG:4326'::character varying,
    native_srs character varying(50) COLLATE pg_catalog."default",
    native_bbox jsonb,
    lat_lon_bbox jsonb,
    grid_info jsonb,
    bands_info jsonb,
    enabled boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT geoserver_coverages_pkey PRIMARY KEY (id),
    CONSTRAINT geoserver_coverages_store_id_name_key UNIQUE (store_id, name),
    CONSTRAINT geoserver_coverages_store_id_fkey FOREIGN KEY (store_id)
        REFERENCES public.geoserver_stores (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)
CREATE TABLE IF NOT EXISTS public.geoserver_featuretypes
(
    id integer NOT NULL DEFAULT nextval('geoserver_featuretypes_id_seq'::regclass),
    name character varying(100) COLLATE pg_catalog."default" NOT NULL,
    native_name character varying(100) COLLATE pg_catalog."default",
    store_id integer,
    title character varying(255) COLLATE pg_catalog."default",
    abstract text COLLATE pg_catalog."default",
    keywords text[] COLLATE pg_catalog."default",
    srs character varying(50) COLLATE pg_catalog."default",
    native_bbox jsonb,
    lat_lon_bbox jsonb,
    attributes jsonb,
    enabled boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT geoserver_featuretypes_pkey PRIMARY KEY (id),
    CONSTRAINT geoserver_featuretypes_store_id_name_key UNIQUE (store_id, name),
    CONSTRAINT geoserver_featuretypes_store_id_fkey FOREIGN KEY (store_id)
        REFERENCES public.geoserver_stores (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)
CREATE TABLE IF NOT EXISTS public.geoserver_layergroups
(
    id integer NOT NULL DEFAULT nextval('geoserver_layergroups_id_seq'::regclass),
    name character varying(100) COLLATE pg_catalog."default" NOT NULL,
    workspace_id integer,
    title character varying(255) COLLATE pg_catalog."default",
    abstract text COLLATE pg_catalog."default",
    mode character varying(50) COLLATE pg_catalog."default" DEFAULT 'SINGLE'::character varying,
    layers jsonb,
    bounds jsonb,
    enabled boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT geoserver_layergroups_pkey PRIMARY KEY (id),
    CONSTRAINT geoserver_layergroups_workspace_id_name_key UNIQUE (workspace_id, name),
    CONSTRAINT geoserver_layergroups_workspace_id_fkey FOREIGN KEY (workspace_id)
        REFERENCES public.geoserver_workspaces (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)
CREATE TABLE IF NOT EXISTS public.geoserver_layers
(
    id integer NOT NULL DEFAULT nextval('geoserver_layers_id_seq'::regclass),
    name character varying(100) COLLATE pg_catalog."default" NOT NULL,
    workspace_id integer,
    featuretype_id integer,
    title character varying(255) COLLATE pg_catalog."default",
    abstract text COLLATE pg_catalog."default",
    default_style character varying(100) COLLATE pg_catalog."default",
    additional_styles text[] COLLATE pg_catalog."default",
    enabled boolean DEFAULT true,
    queryable boolean DEFAULT true,
    opaque boolean DEFAULT false,
    attribution text COLLATE pg_catalog."default",
    wms_url text COLLATE pg_catalog."default",
    wfs_url text COLLATE pg_catalog."default",
    wcs_url text COLLATE pg_catalog."default",
    file_id integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    coverage_id integer,
    CONSTRAINT geoserver_layers_pkey PRIMARY KEY (id),
    CONSTRAINT geoserver_layers_workspace_id_name_key UNIQUE (workspace_id, name),
    CONSTRAINT geoserver_layers_coverage_id_fkey FOREIGN KEY (coverage_id)
        REFERENCES public.geoserver_coverages (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE,
    CONSTRAINT geoserver_layers_featuretype_id_fkey FOREIGN KEY (featuretype_id)
        REFERENCES public.geoserver_featuretypes (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE,
    CONSTRAINT geoserver_layers_file_id_fkey FOREIGN KEY (file_id)
        REFERENCES public.files (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT geoserver_layers_workspace_id_fkey FOREIGN KEY (workspace_id)
        REFERENCES public.geoserver_workspaces (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE,
    CONSTRAINT check_data_source CHECK (featuretype_id IS NOT NULL AND coverage_id IS NULL OR featuretype_id IS NULL AND coverage_id IS NOT NULL)
)
CREATE TABLE IF NOT EXISTS public.geoserver_stores
(
    id integer NOT NULL DEFAULT nextval('geoserver_stores_id_seq'::regclass),
    name character varying(100) COLLATE pg_catalog."default" NOT NULL,
    workspace_id integer,
    store_type character varying(50) COLLATE pg_catalog."default" NOT NULL,
    data_type character varying(50) COLLATE pg_catalog."default",
    connection_params jsonb,
    description text COLLATE pg_catalog."default",
    enabled boolean DEFAULT true,
    file_id integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT geoserver_stores_pkey PRIMARY KEY (id),
    CONSTRAINT geoserver_stores_workspace_id_name_key UNIQUE (workspace_id, name),
    CONSTRAINT geoserver_stores_file_id_fkey FOREIGN KEY (file_id)
        REFERENCES public.files (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT geoserver_stores_workspace_id_fkey FOREIGN KEY (workspace_id)
        REFERENCES public.geoserver_workspaces (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)
CREATE TABLE IF NOT EXISTS public.geoserver_styles
(
    id integer NOT NULL DEFAULT nextval('geoserver_styles_id_seq'::regclass),
    name character varying(100) COLLATE pg_catalog."default" NOT NULL,
    workspace_id integer,
    filename character varying(255) COLLATE pg_catalog."default",
    format character varying(50) COLLATE pg_catalog."default" DEFAULT 'sld'::character varying,
    language_version character varying(20) COLLATE pg_catalog."default",
    content text COLLATE pg_catalog."default",
    description text COLLATE pg_catalog."default",
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT geoserver_styles_pkey PRIMARY KEY (id),
    CONSTRAINT geoserver_styles_workspace_id_name_key UNIQUE (workspace_id, name),
    CONSTRAINT geoserver_styles_workspace_id_fkey FOREIGN KEY (workspace_id)
        REFERENCES public.geoserver_workspaces (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)
CREATE TABLE IF NOT EXISTS public.geoserver_workspaces
(
    id integer NOT NULL DEFAULT nextval('geoserver_workspaces_id_seq'::regclass),
    name character varying(100) COLLATE pg_catalog."default" NOT NULL,
    namespace_uri character varying(255) COLLATE pg_catalog."default",
    namespace_prefix character varying(100) COLLATE pg_catalog."default",
    description text COLLATE pg_catalog."default",
    is_default boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT geoserver_workspaces_pkey PRIMARY KEY (id),
    CONSTRAINT geoserver_workspaces_name_key UNIQUE (name)
)