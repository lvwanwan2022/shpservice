--
-- PostgreSQL database dump
--

-- Dumped from database version 16.3
-- Dumped by pg_dump version 16.3

-- Started on 2025-06-16 10:52:41

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 219 (class 1259 OID 17066)
-- Name: files; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.files (
    id integer NOT NULL,
    file_name character varying(100) NOT NULL,
    file_path character varying(200) NOT NULL,
    original_name character varying(100) NOT NULL,
    file_size bigint NOT NULL,
    is_public boolean DEFAULT true,
    discipline character varying(50) NOT NULL,
    dimension character varying(10) NOT NULL,
    file_type character varying(20) NOT NULL,
    coordinate_system character varying(20),
    tags character varying(200),
    description text,
    user_id integer,
    upload_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    status character varying(20) DEFAULT 'uploaded'::character varying,
    bbox jsonb,
    geometry_type character varying(50),
    feature_count integer,
    metadata jsonb
);


ALTER TABLE public.files OWNER TO postgres;

--
-- TOC entry 218 (class 1259 OID 17065)
-- Name: files_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.files_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.files_id_seq OWNER TO postgres;

--
-- TOC entry 6059 (class 0 OID 0)
-- Dependencies: 218
-- Name: files_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.files_id_seq OWNED BY public.files.id;


--
-- TOC entry 245 (class 1259 OID 23522)
-- Name: geojson_12; Type: TABLE; Schema: public; Owner: postgres
--

--
-- TOC entry 237 (class 1259 OID 17271)
-- Name: geoserver_coverages; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.geoserver_coverages (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    native_name character varying(100),
    store_id integer,
    title character varying(255),
    abstract text,
    keywords text[],
    srs character varying(50) DEFAULT 'EPSG:4326'::character varying,
    native_srs character varying(50),
    native_bbox jsonb,
    lat_lon_bbox jsonb,
    grid_info jsonb,
    bands_info jsonb,
    enabled boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.geoserver_coverages OWNER TO postgres;

--
-- TOC entry 236 (class 1259 OID 17270)
-- Name: geoserver_coverages_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.geoserver_coverages_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.geoserver_coverages_id_seq OWNER TO postgres;

--
-- TOC entry 6065 (class 0 OID 0)
-- Dependencies: 236
-- Name: geoserver_coverages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.geoserver_coverages_id_seq OWNED BY public.geoserver_coverages.id;


--
-- TOC entry 227 (class 1259 OID 17158)
-- Name: geoserver_featuretypes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.geoserver_featuretypes (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    native_name character varying(100),
    store_id integer,
    title character varying(255),
    abstract text,
    keywords text[],
    srs character varying(50),
    native_bbox jsonb,
    lat_lon_bbox jsonb,
    attributes jsonb,
    enabled boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    projection_policy character varying(50) DEFAULT 'REPROJECT_TO_DECLARED'::character varying
);


ALTER TABLE public.geoserver_featuretypes OWNER TO postgres;

--
-- TOC entry 226 (class 1259 OID 17157)
-- Name: geoserver_featuretypes_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.geoserver_featuretypes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.geoserver_featuretypes_id_seq OWNER TO postgres;

--
-- TOC entry 6066 (class 0 OID 0)
-- Dependencies: 226
-- Name: geoserver_featuretypes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.geoserver_featuretypes_id_seq OWNED BY public.geoserver_featuretypes.id;


--
-- TOC entry 233 (class 1259 OID 17227)
-- Name: geoserver_layergroups; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.geoserver_layergroups (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    workspace_id integer,
    title character varying(255),
    abstract text,
    mode character varying(50) DEFAULT 'SINGLE'::character varying,
    layers jsonb,
    bounds jsonb,
    enabled boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.geoserver_layergroups OWNER TO postgres;

--
-- TOC entry 232 (class 1259 OID 17226)
-- Name: geoserver_layergroups_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.geoserver_layergroups_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.geoserver_layergroups_id_seq OWNER TO postgres;

--
-- TOC entry 6067 (class 0 OID 0)
-- Dependencies: 232
-- Name: geoserver_layergroups_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.geoserver_layergroups_id_seq OWNED BY public.geoserver_layergroups.id;


--
-- TOC entry 229 (class 1259 OID 17177)
-- Name: geoserver_layers; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.geoserver_layers (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    workspace_id integer,
    featuretype_id integer,
    title character varying(255),
    abstract text,
    default_style character varying(100),
    additional_styles text[],
    enabled boolean DEFAULT true,
    queryable boolean DEFAULT true,
    opaque boolean DEFAULT false,
    attribution text,
    wms_url text,
    wfs_url text,
    wcs_url text,
    file_id integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    coverage_id integer,
    style_config jsonb,
    CONSTRAINT check_data_source CHECK ((((featuretype_id IS NOT NULL) AND (coverage_id IS NULL)) OR ((featuretype_id IS NULL) AND (coverage_id IS NOT NULL))))
);


ALTER TABLE public.geoserver_layers OWNER TO postgres;

--
-- TOC entry 228 (class 1259 OID 17176)
-- Name: geoserver_layers_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.geoserver_layers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.geoserver_layers_id_seq OWNER TO postgres;

--
-- TOC entry 6068 (class 0 OID 0)
-- Dependencies: 228
-- Name: geoserver_layers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.geoserver_layers_id_seq OWNED BY public.geoserver_layers.id;


--
-- TOC entry 225 (class 1259 OID 17134)
-- Name: geoserver_stores; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.geoserver_stores (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    workspace_id integer,
    store_type character varying(50) NOT NULL,
    data_type character varying(50),
    connection_params jsonb,
    description text,
    enabled boolean DEFAULT true,
    file_id integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.geoserver_stores OWNER TO postgres;

--
-- TOC entry 224 (class 1259 OID 17133)
-- Name: geoserver_stores_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.geoserver_stores_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.geoserver_stores_id_seq OWNER TO postgres;

--
-- TOC entry 6069 (class 0 OID 0)
-- Dependencies: 224
-- Name: geoserver_stores_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.geoserver_stores_id_seq OWNED BY public.geoserver_stores.id;


--
-- TOC entry 231 (class 1259 OID 17208)
-- Name: geoserver_styles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.geoserver_styles (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    workspace_id integer,
    filename character varying(255),
    format character varying(50) DEFAULT 'sld'::character varying,
    language_version character varying(20),
    content text,
    description text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.geoserver_styles OWNER TO postgres;

--
-- TOC entry 230 (class 1259 OID 17207)
-- Name: geoserver_styles_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.geoserver_styles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.geoserver_styles_id_seq OWNER TO postgres;

--
-- TOC entry 6070 (class 0 OID 0)
-- Dependencies: 230
-- Name: geoserver_styles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.geoserver_styles_id_seq OWNED BY public.geoserver_styles.id;


--
-- TOC entry 223 (class 1259 OID 17120)
-- Name: geoserver_workspaces; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.geoserver_workspaces (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    namespace_uri character varying(255),
    namespace_prefix character varying(100),
    description text,
    is_default boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.geoserver_workspaces OWNER TO postgres;

--
-- TOC entry 222 (class 1259 OID 17119)
-- Name: geoserver_workspaces_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.geoserver_workspaces_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.geoserver_workspaces_id_seq OWNER TO postgres;

--
-- TOC entry 6071 (class 0 OID 0)
-- Dependencies: 222
-- Name: geoserver_workspaces_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.geoserver_workspaces_id_seq OWNED BY public.geoserver_workspaces.id;


--
-- TOC entry 235 (class 1259 OID 17247)
-- Name: scene_layers; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.scene_layers (
    id integer NOT NULL,
    scene_id integer,
    layer_id integer,
    layer_order integer DEFAULT 0,
    visible boolean DEFAULT true,
    opacity numeric(3,2) DEFAULT 1.0,
    style_name character varying(100),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    custom_style jsonb,
    queryable boolean DEFAULT true,
    selectable boolean DEFAULT true,
    layer_type character varying(20) DEFAULT 'geoserver'::character varying,
    service_reference character varying(100),
    service_url text,
    martin_service_id integer,
    martin_service_type character varying(20) DEFAULT NULL::character varying,
    CONSTRAINT chk_layer_type CHECK (((layer_type)::text = ANY ((ARRAY['geoserver'::character varying, 'martin'::character varying])::text[])))
);


ALTER TABLE public.scene_layers OWNER TO postgres;

--
-- TOC entry 6072 (class 0 OID 0)
-- Dependencies: 235
-- Name: COLUMN scene_layers.layer_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.scene_layers.layer_id IS '图层ID：当martin_service_id不为空时，此字段可为虚拟ID；否则为GeoServer图层ID';


--
-- TOC entry 6073 (class 0 OID 0)
-- Dependencies: 235
-- Name: COLUMN scene_layers.martin_service_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.scene_layers.martin_service_id IS 'Martin服务ID，当图层类型为Martin服务时，通过此字段关联到geojson_martin_services表';


--
-- TOC entry 234 (class 1259 OID 17246)
-- Name: scene_layers_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.scene_layers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.scene_layers_id_seq OWNER TO postgres;

--
-- TOC entry 6074 (class 0 OID 0)
-- Dependencies: 234
-- Name: scene_layers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.scene_layers_id_seq OWNED BY public.scene_layers.id;


--
-- TOC entry 221 (class 1259 OID 17082)
-- Name: scenes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.scenes (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    is_public boolean DEFAULT true,
    user_id integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.scenes OWNER TO postgres;

--
-- TOC entry 220 (class 1259 OID 17081)
-- Name: scenes_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.scenes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.scenes_id_seq OWNER TO postgres;

--
-- TOC entry 6075 (class 0 OID 0)
-- Dependencies: 220
-- Name: scenes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.scenes_id_seq OWNED BY public.scenes.id;


--
-- TOC entry 217 (class 1259 OID 17056)
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(50) NOT NULL,
    password character varying(100) NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.users OWNER TO postgres;

--
-- TOC entry 216 (class 1259 OID 17055)
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO postgres;

--
-- TOC entry 6076 (class 0 OID 0)
-- Dependencies: 216
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- TOC entry 238 (class 1259 OID 17305)
-- Name: v_layer_info; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.v_layer_info AS
 SELECT gl.id AS layer_id,
    gl.name AS layer_name,
    gl.title,
    gl.abstract,
    gw.name AS workspace_name,
    gl.wms_url,
    gl.wfs_url,
    gl.wcs_url,
    gl.enabled,
    gl.queryable,
    f.id AS file_id,
    f.file_name,
    f.file_type,
    f.file_size,
    f.dimension,
    f.discipline,
    f.coordinate_system,
    f.bbox AS file_bbox,
    f.geometry_type,
    f.feature_count,
    f.status AS file_status,
    gs.name AS store_name,
    gs.store_type,
    gs.data_type,
        CASE
            WHEN (gft.id IS NOT NULL) THEN 'vector'::text
            WHEN (gc.id IS NOT NULL) THEN 'raster'::text
            ELSE 'unknown'::text
        END AS data_source_type,
    COALESCE(gft.srs, gc.srs) AS srs,
    COALESCE(gft.lat_lon_bbox, gc.lat_lon_bbox) AS lat_lon_bbox,
    gl.created_at,
    gl.updated_at
   FROM (((((public.geoserver_layers gl
     LEFT JOIN public.geoserver_workspaces gw ON ((gl.workspace_id = gw.id)))
     LEFT JOIN public.files f ON ((gl.file_id = f.id)))
     LEFT JOIN public.geoserver_featuretypes gft ON ((gl.featuretype_id = gft.id)))
     LEFT JOIN public.geoserver_coverages gc ON ((gl.coverage_id = gc.id)))
     LEFT JOIN public.geoserver_stores gs ON (((gft.store_id = gs.id) OR (gc.store_id = gs.id))));


ALTER VIEW public.v_layer_info OWNER TO postgres;

--
-- TOC entry 258 (class 1259 OID 23798)
-- Name: vector_martin_services_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.vector_martin_services_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.vector_martin_services_id_seq OWNER TO postgres;

--
-- TOC entry 5750 (class 2604 OID 17069)
-- Name: files id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.files ALTER COLUMN id SET DEFAULT nextval('public.files_id_seq'::regclass);


--
-- TOC entry 5795 (class 2604 OID 17274)
-- Name: geoserver_coverages id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.geoserver_coverages ALTER COLUMN id SET DEFAULT nextval('public.geoserver_coverages_id_seq'::regclass);


--
-- TOC entry 5766 (class 2604 OID 17161)
-- Name: geoserver_featuretypes id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.geoserver_featuretypes ALTER COLUMN id SET DEFAULT nextval('public.geoserver_featuretypes_id_seq'::regclass);


--
-- TOC entry 5781 (class 2604 OID 17230)
-- Name: geoserver_layergroups id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.geoserver_layergroups ALTER COLUMN id SET DEFAULT nextval('public.geoserver_layergroups_id_seq'::regclass);


--
-- TOC entry 5771 (class 2604 OID 17180)
-- Name: geoserver_layers id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.geoserver_layers ALTER COLUMN id SET DEFAULT nextval('public.geoserver_layers_id_seq'::regclass);


--
-- TOC entry 5762 (class 2604 OID 17137)
-- Name: geoserver_stores id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.geoserver_stores ALTER COLUMN id SET DEFAULT nextval('public.geoserver_stores_id_seq'::regclass);


--
-- TOC entry 5777 (class 2604 OID 17211)
-- Name: geoserver_styles id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.geoserver_styles ALTER COLUMN id SET DEFAULT nextval('public.geoserver_styles_id_seq'::regclass);


--
-- TOC entry 5758 (class 2604 OID 17123)
-- Name: geoserver_workspaces id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.geoserver_workspaces ALTER COLUMN id SET DEFAULT nextval('public.geoserver_workspaces_id_seq'::regclass);


--
-- TOC entry 5786 (class 2604 OID 17250)
-- Name: scene_layers id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.scene_layers ALTER COLUMN id SET DEFAULT nextval('public.scene_layers_id_seq'::regclass);


--
-- TOC entry 5754 (class 2604 OID 17085)
-- Name: scenes id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.scenes ALTER COLUMN id SET DEFAULT nextval('public.scenes_id_seq'::regclass);


--
-- TOC entry 5748 (class 2604 OID 17059)
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- TOC entry 5818 (class 2606 OID 17075)
-- Name: files files_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.files
    ADD CONSTRAINT files_pkey PRIMARY KEY (id);



--
-- TOC entry 5860 (class 2606 OID 17282)
-- Name: geoserver_coverages geoserver_coverages_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.geoserver_coverages
    ADD CONSTRAINT geoserver_coverages_pkey PRIMARY KEY (id);


--
-- TOC entry 5862 (class 2606 OID 17284)
-- Name: geoserver_coverages geoserver_coverages_store_id_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.geoserver_coverages
    ADD CONSTRAINT geoserver_coverages_store_id_name_key UNIQUE (store_id, name);


--
-- TOC entry 5832 (class 2606 OID 17168)
-- Name: geoserver_featuretypes geoserver_featuretypes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.geoserver_featuretypes
    ADD CONSTRAINT geoserver_featuretypes_pkey PRIMARY KEY (id);


--
-- TOC entry 5834 (class 2606 OID 17170)
-- Name: geoserver_featuretypes geoserver_featuretypes_store_id_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.geoserver_featuretypes
    ADD CONSTRAINT geoserver_featuretypes_store_id_name_key UNIQUE (store_id, name);


--
-- TOC entry 5844 (class 2606 OID 17238)
-- Name: geoserver_layergroups geoserver_layergroups_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.geoserver_layergroups
    ADD CONSTRAINT geoserver_layergroups_pkey PRIMARY KEY (id);


--
-- TOC entry 5846 (class 2606 OID 17240)
-- Name: geoserver_layergroups geoserver_layergroups_workspace_id_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.geoserver_layergroups
    ADD CONSTRAINT geoserver_layergroups_workspace_id_name_key UNIQUE (workspace_id, name);


--
-- TOC entry 5836 (class 2606 OID 17189)
-- Name: geoserver_layers geoserver_layers_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.geoserver_layers
    ADD CONSTRAINT geoserver_layers_pkey PRIMARY KEY (id);


--
-- TOC entry 5838 (class 2606 OID 17191)
-- Name: geoserver_layers geoserver_layers_workspace_id_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.geoserver_layers
    ADD CONSTRAINT geoserver_layers_workspace_id_name_key UNIQUE (workspace_id, name);


--
-- TOC entry 5828 (class 2606 OID 17144)
-- Name: geoserver_stores geoserver_stores_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.geoserver_stores
    ADD CONSTRAINT geoserver_stores_pkey PRIMARY KEY (id);


--
-- TOC entry 5830 (class 2606 OID 17146)
-- Name: geoserver_stores geoserver_stores_workspace_id_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.geoserver_stores
    ADD CONSTRAINT geoserver_stores_workspace_id_name_key UNIQUE (workspace_id, name);


--
-- TOC entry 5840 (class 2606 OID 17218)
-- Name: geoserver_styles geoserver_styles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.geoserver_styles
    ADD CONSTRAINT geoserver_styles_pkey PRIMARY KEY (id);


--
-- TOC entry 5842 (class 2606 OID 17220)
-- Name: geoserver_styles geoserver_styles_workspace_id_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.geoserver_styles
    ADD CONSTRAINT geoserver_styles_workspace_id_name_key UNIQUE (workspace_id, name);


--
-- TOC entry 5824 (class 2606 OID 17132)
-- Name: geoserver_workspaces geoserver_workspaces_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.geoserver_workspaces
    ADD CONSTRAINT geoserver_workspaces_name_key UNIQUE (name);


--
-- TOC entry 5826 (class 2606 OID 17130)
-- Name: geoserver_workspaces geoserver_workspaces_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.geoserver_workspaces
    ADD CONSTRAINT geoserver_workspaces_pkey PRIMARY KEY (id);


--
-- TOC entry 5856 (class 2606 OID 17256)
-- Name: scene_layers scene_layers_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.scene_layers
    ADD CONSTRAINT scene_layers_pkey PRIMARY KEY (id);


--
-- TOC entry 5858 (class 2606 OID 23297)
-- Name: scene_layers scene_layers_scene_id_layer_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.scene_layers
    ADD CONSTRAINT scene_layers_scene_id_layer_id_key UNIQUE (scene_id, layer_id);


--
-- TOC entry 5822 (class 2606 OID 17092)
-- Name: scenes scenes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.scenes
    ADD CONSTRAINT scenes_pkey PRIMARY KEY (id);


--
-- TOC entry 5814 (class 2606 OID 17062)
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- TOC entry 5816 (class 2606 OID 17064)
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- TOC entry 5819 (class 1259 OID 17302)
-- Name: idx_files_file_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_files_file_type ON public.files USING btree (file_type);


--
-- TOC entry 5820 (class 1259 OID 17301)
-- Name: idx_files_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_files_status ON public.files USING btree (status);


--
-- TOC entry 5882 (class 1259 OID 33639)
-- Name: idx_geojson_files_file_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_geojson_files_file_id ON public.geojson_files USING btree (file_id);


--
-- TOC entry 5883 (class 1259 OID 33640)
-- Name: idx_geojson_files_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_geojson_files_status ON public.geojson_files USING btree (status);


--
-- TOC entry 5884 (class 1259 OID 33642)
-- Name: idx_geojson_files_upload_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_geojson_files_upload_date ON public.geojson_files USING btree (upload_date);


--
-- TOC entry 5885 (class 1259 OID 33641)
-- Name: idx_geojson_files_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_geojson_files_user_id ON public.geojson_files USING btree (user_id);


--
-- TOC entry 5863 (class 1259 OID 17303)
-- Name: idx_geoserver_coverages_store_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_geoserver_coverages_store_id ON public.geoserver_coverages USING btree (store_id);


--
-- TOC entry 5847 (class 1259 OID 23370)
-- Name: idx_scene_layers_layer_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_scene_layers_layer_id ON public.scene_layers USING btree (layer_id);


--
-- TOC entry 5848 (class 1259 OID 23371)
-- Name: idx_scene_layers_layer_order; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_scene_layers_layer_order ON public.scene_layers USING btree (layer_order);


--
-- TOC entry 5849 (class 1259 OID 23368)
-- Name: idx_scene_layers_martin_service_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_scene_layers_martin_service_id ON public.scene_layers USING btree (martin_service_id);


--
-- TOC entry 5850 (class 1259 OID 17304)
-- Name: idx_scene_layers_order; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_scene_layers_order ON public.scene_layers USING btree (scene_id, layer_order);


--
-- TOC entry 5851 (class 1259 OID 23311)
-- Name: idx_scene_layers_reference; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_scene_layers_reference ON public.scene_layers USING btree (service_reference);


--
-- TOC entry 5852 (class 1259 OID 23369)
-- Name: idx_scene_layers_scene_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_scene_layers_scene_id ON public.scene_layers USING btree (scene_id);


--
-- TOC entry 5853 (class 1259 OID 23312)
-- Name: idx_scene_layers_scene_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_scene_layers_scene_type ON public.scene_layers USING btree (scene_id, layer_type);


--
-- TOC entry 5854 (class 1259 OID 23310)
-- Name: idx_scene_layers_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_scene_layers_type ON public.scene_layers USING btree (layer_type);


--
-- TOC entry 5890 (class 2606 OID 17076)
-- Name: files files_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.files
    ADD CONSTRAINT files_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 5901 (class 2606 OID 23823)
-- Name: scene_layers fk_scene_layers_vector_martin_service; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.scene_layers
    ADD CONSTRAINT fk_scene_layers_vector_martin_service FOREIGN KEY (martin_service_id) REFERENCES public.vector_martin_services(id) ON DELETE CASCADE;




--
-- TOC entry 5903 (class 2606 OID 17285)
-- Name: geoserver_coverages geoserver_coverages_store_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.geoserver_coverages
    ADD CONSTRAINT geoserver_coverages_store_id_fkey FOREIGN KEY (store_id) REFERENCES public.geoserver_stores(id) ON DELETE CASCADE;


--
-- TOC entry 5894 (class 2606 OID 17171)
-- Name: geoserver_featuretypes geoserver_featuretypes_store_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.geoserver_featuretypes
    ADD CONSTRAINT geoserver_featuretypes_store_id_fkey FOREIGN KEY (store_id) REFERENCES public.geoserver_stores(id) ON DELETE CASCADE;


--
-- TOC entry 5900 (class 2606 OID 17241)
-- Name: geoserver_layergroups geoserver_layergroups_workspace_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.geoserver_layergroups
    ADD CONSTRAINT geoserver_layergroups_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.geoserver_workspaces(id) ON DELETE CASCADE;


--
-- TOC entry 5895 (class 2606 OID 17290)
-- Name: geoserver_layers geoserver_layers_coverage_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.geoserver_layers
    ADD CONSTRAINT geoserver_layers_coverage_id_fkey FOREIGN KEY (coverage_id) REFERENCES public.geoserver_coverages(id) ON DELETE CASCADE;


--
-- TOC entry 5896 (class 2606 OID 17197)
-- Name: geoserver_layers geoserver_layers_featuretype_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.geoserver_layers
    ADD CONSTRAINT geoserver_layers_featuretype_id_fkey FOREIGN KEY (featuretype_id) REFERENCES public.geoserver_featuretypes(id) ON DELETE CASCADE;


--
-- TOC entry 5897 (class 2606 OID 17202)
-- Name: geoserver_layers geoserver_layers_file_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.geoserver_layers
    ADD CONSTRAINT geoserver_layers_file_id_fkey FOREIGN KEY (file_id) REFERENCES public.files(id);


--
-- TOC entry 5898 (class 2606 OID 17192)
-- Name: geoserver_layers geoserver_layers_workspace_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.geoserver_layers
    ADD CONSTRAINT geoserver_layers_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.geoserver_workspaces(id) ON DELETE CASCADE;


--
-- TOC entry 5892 (class 2606 OID 17152)
-- Name: geoserver_stores geoserver_stores_file_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.geoserver_stores
    ADD CONSTRAINT geoserver_stores_file_id_fkey FOREIGN KEY (file_id) REFERENCES public.files(id);


--
-- TOC entry 5893 (class 2606 OID 17147)
-- Name: geoserver_stores geoserver_stores_workspace_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.geoserver_stores
    ADD CONSTRAINT geoserver_stores_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.geoserver_workspaces(id) ON DELETE CASCADE;


--
-- TOC entry 5899 (class 2606 OID 17221)
-- Name: geoserver_styles geoserver_styles_workspace_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.geoserver_styles
    ADD CONSTRAINT geoserver_styles_workspace_id_fkey FOREIGN KEY (workspace_id) REFERENCES public.geoserver_workspaces(id) ON DELETE CASCADE;


--
-- TOC entry 5902 (class 2606 OID 17259)
-- Name: scene_layers scene_layers_scene_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.scene_layers
    ADD CONSTRAINT scene_layers_scene_id_fkey FOREIGN KEY (scene_id) REFERENCES public.scenes(id) ON DELETE CASCADE;


--
-- TOC entry 5891 (class 2606 OID 17093)
-- Name: scenes scenes_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.scenes
    ADD CONSTRAINT scenes_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


-- Completed on 2025-06-16 10:52:41

--
-- PostgreSQL database dump complete
--

