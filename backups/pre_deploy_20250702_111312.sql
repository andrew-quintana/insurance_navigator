

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;


CREATE SCHEMA IF NOT EXISTS "monitoring";


ALTER SCHEMA "monitoring" OWNER TO "postgres";


COMMENT ON SCHEMA "public" IS 'standard public schema';



CREATE EXTENSION IF NOT EXISTS "pg_graphql" WITH SCHEMA "graphql";






CREATE EXTENSION IF NOT EXISTS "pg_stat_statements" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "pgcrypto" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "supabase_vault" WITH SCHEMA "vault";






CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA "extensions";






CREATE OR REPLACE FUNCTION "monitoring"."create_alert"("p_type" "text", "p_severity" "text", "p_message" "text", "p_metadata" "jsonb" DEFAULT '{}'::"jsonb") RETURNS "uuid"
    LANGUAGE "plpgsql"
    AS $$
    DECLARE
        v_alert_id UUID;
    BEGIN
        INSERT INTO monitoring.alerts (alert_type, severity, message, metadata)
        VALUES (p_type, p_severity, p_message, p_metadata)
        RETURNING id INTO v_alert_id;
        
        -- Here you would typically call a notification service
        -- This is just a placeholder
        RAISE NOTICE 'Alert created: %', p_message;
        
        RETURN v_alert_id;
    END;
    $$;


ALTER FUNCTION "monitoring"."create_alert"("p_type" "text", "p_severity" "text", "p_message" "text", "p_metadata" "jsonb") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "monitoring"."log_slow_query"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$
    BEGIN
        IF NEW.execution_time > interval '1 second' THEN
            INSERT INTO monitoring.error_logs 
                (error_type, error_message, context)
            VALUES 
                ('slow_query', 
                 format('Query took %s seconds', extract(epoch from NEW.execution_time)),
                 jsonb_build_object('query', NEW.query_text, 'rows_affected', NEW.rows_affected));
        END IF;
        RETURN NEW;
    END;
    $$;


ALTER FUNCTION "monitoring"."log_slow_query"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."update_updated_at_column"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


ALTER FUNCTION "public"."update_updated_at_column"() OWNER TO "postgres";

SET default_tablespace = '';

SET default_table_access_method = "heap";


CREATE TABLE IF NOT EXISTS "monitoring"."alerts" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "alert_type" "text",
    "severity" "text",
    "message" "text",
    "timestamp" timestamp with time zone DEFAULT "now"(),
    "acknowledged" boolean DEFAULT false,
    "acknowledged_by" "uuid",
    "acknowledged_at" timestamp with time zone,
    "metadata" "jsonb"
);


ALTER TABLE "monitoring"."alerts" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "monitoring"."edge_function_logs" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "function_name" "text",
    "execution_time" interval,
    "memory_used" integer,
    "status" "text",
    "error_message" "text",
    "timestamp" timestamp with time zone DEFAULT "now"(),
    "request_id" "uuid",
    "metadata" "jsonb"
);


ALTER TABLE "monitoring"."edge_function_logs" OWNER TO "postgres";


CREATE OR REPLACE VIEW "monitoring"."edge_function_metrics" AS
 SELECT "function_name",
    "count"(*) AS "total_executions",
    "avg"(EXTRACT(epoch FROM "execution_time")) AS "avg_execution_time",
    "max"(EXTRACT(epoch FROM "execution_time")) AS "max_execution_time",
    "min"(EXTRACT(epoch FROM "execution_time")) AS "min_execution_time",
    "avg"("memory_used") AS "avg_memory_used",
    "count"(*) FILTER (WHERE ("status" = 'error'::"text")) AS "error_count"
   FROM "monitoring"."edge_function_logs"
  WHERE ("timestamp" > ("now"() - '24:00:00'::interval))
  GROUP BY "function_name";


ALTER VIEW "monitoring"."edge_function_metrics" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "monitoring"."error_logs" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "error_type" "text",
    "error_message" "text",
    "error_stack" "text",
    "timestamp" timestamp with time zone DEFAULT "now"(),
    "context" "jsonb"
);


ALTER TABLE "monitoring"."error_logs" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "monitoring"."processing_logs" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "document_id" "uuid",
    "stage" "text",
    "status" "text",
    "processing_time" interval,
    "error_message" "text",
    "timestamp" timestamp with time zone DEFAULT "now"(),
    "metadata" "jsonb"
);


ALTER TABLE "monitoring"."processing_logs" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "monitoring"."query_logs" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "query_text" "text",
    "execution_time" interval,
    "rows_affected" integer,
    "timestamp" timestamp with time zone DEFAULT "now"(),
    "user_id" "uuid",
    "client_info" "jsonb"
);


ALTER TABLE "monitoring"."query_logs" OWNER TO "postgres";


CREATE OR REPLACE VIEW "monitoring"."performance_dashboard" AS
 SELECT 'database'::"text" AS "component",
    "jsonb_build_object"('slow_queries', ( SELECT "count"(*) AS "count"
           FROM "monitoring"."query_logs"
          WHERE ("query_logs"."execution_time" > '00:00:01'::interval)), 'avg_query_time', ( SELECT "avg"(EXTRACT(epoch FROM "query_logs"."execution_time")) AS "avg"
           FROM "monitoring"."query_logs")) AS "metrics"
UNION ALL
 SELECT 'edge_functions'::"text" AS "component",
    "jsonb_build_object"('total_executions', "count"(*), 'error_rate', (("count"(*) FILTER (WHERE ("edge_function_logs"."status" = 'error'::"text")))::double precision / ("count"(*))::double precision)) AS "metrics"
   FROM "monitoring"."edge_function_logs"
UNION ALL
 SELECT 'document_processing'::"text" AS "component",
    "jsonb_build_object"('total_documents', "count"(*), 'success_rate', (("count"(*) FILTER (WHERE ("processing_logs"."status" = 'success'::"text")))::double precision / ("count"(*))::double precision)) AS "metrics"
   FROM "monitoring"."processing_logs";


ALTER VIEW "monitoring"."performance_dashboard" OWNER TO "postgres";


CREATE OR REPLACE VIEW "monitoring"."performance_metrics" AS
 SELECT "schemaname",
    "relname",
    "seq_scan",
    "seq_tup_read",
    "idx_scan",
    "idx_tup_fetch",
    "n_tup_ins",
    "n_tup_upd",
    "n_tup_del",
    "n_live_tup",
    "n_dead_tup",
    "last_vacuum",
    "last_autovacuum",
    "last_analyze",
    "last_autoanalyze"
   FROM "pg_stat_user_tables";


ALTER VIEW "monitoring"."performance_metrics" OWNER TO "postgres";


CREATE OR REPLACE VIEW "monitoring"."processing_metrics" AS
 SELECT "stage",
    "count"(*) AS "total_documents",
    "avg"(EXTRACT(epoch FROM "processing_time")) AS "avg_processing_time",
    "count"(*) FILTER (WHERE ("status" = 'error'::"text")) AS "error_count",
    "count"(*) FILTER (WHERE ("status" = 'success'::"text")) AS "success_count"
   FROM "monitoring"."processing_logs"
  WHERE ("timestamp" > ("now"() - '24:00:00'::interval))
  GROUP BY "stage";


ALTER VIEW "monitoring"."processing_metrics" OWNER TO "postgres";


CREATE OR REPLACE VIEW "monitoring"."system_health" AS
 SELECT ( SELECT "count"(*) AS "count"
           FROM "monitoring"."error_logs"
          WHERE ("error_logs"."timestamp" > ("now"() - '01:00:00'::interval))) AS "recent_errors",
    ( SELECT "count"(*) AS "count"
           FROM "monitoring"."alerts"
          WHERE (NOT "alerts"."acknowledged")) AS "active_alerts",
    ( SELECT "count"(*) AS "count"
           FROM "monitoring"."query_logs"
          WHERE ("query_logs"."execution_time" > '00:00:01'::interval)) AS "slow_queries",
    ( SELECT "count"(*) AS "count"
           FROM "monitoring"."edge_function_logs"
          WHERE ("edge_function_logs"."status" = 'error'::"text")) AS "edge_function_errors";


ALTER VIEW "monitoring"."system_health" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."documents" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "user_id" "uuid",
    "filename" "text" NOT NULL,
    "content_type" "text" NOT NULL,
    "status" "text" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "storage_path" "text" NOT NULL,
    "error_message" "text",
    CONSTRAINT "documents_status_check" CHECK (("status" = ANY (ARRAY['processing'::"text", 'completed'::"text", 'error'::"text"]))),
    CONSTRAINT "valid_content_type" CHECK (("content_type" = ANY (ARRAY['application/pdf'::"text", 'application/msword'::"text", 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'::"text"])))
);


ALTER TABLE "public"."documents" OWNER TO "postgres";


COMMENT ON TABLE "public"."documents" IS 'Document storage with future encryption and audit logging planned';



COMMENT ON COLUMN "public"."documents"."storage_path" IS 'Path to document in storage bucket, follows pattern: documents/{user_id}/{filename}';



CREATE TABLE IF NOT EXISTS "public"."users" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "email" "text" NOT NULL,
    "name" "text" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "last_login" timestamp with time zone,
    "session_expires" timestamp with time zone,
    CONSTRAINT "email_format" CHECK (("email" ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'::"text"))
);


ALTER TABLE "public"."users" OWNER TO "postgres";


COMMENT ON TABLE "public"."users" IS 'User accounts with future HIPAA compliance fields planned';



COMMENT ON COLUMN "public"."users"."id" IS 'Primary identifier for user accounts';



ALTER TABLE ONLY "monitoring"."alerts"
    ADD CONSTRAINT "alerts_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "monitoring"."edge_function_logs"
    ADD CONSTRAINT "edge_function_logs_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "monitoring"."error_logs"
    ADD CONSTRAINT "error_logs_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "monitoring"."processing_logs"
    ADD CONSTRAINT "processing_logs_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "monitoring"."query_logs"
    ADD CONSTRAINT "query_logs_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."documents"
    ADD CONSTRAINT "documents_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."users"
    ADD CONSTRAINT "users_email_key" UNIQUE ("email");



ALTER TABLE ONLY "public"."users"
    ADD CONSTRAINT "users_pkey" PRIMARY KEY ("id");



CREATE INDEX "idx_documents_status" ON "public"."documents" USING "btree" ("status");



CREATE INDEX "idx_documents_user_id" ON "public"."documents" USING "btree" ("user_id");



CREATE INDEX "idx_users_email" ON "public"."users" USING "btree" ("email");



CREATE OR REPLACE TRIGGER "tr_log_slow_query" AFTER INSERT ON "monitoring"."query_logs" FOR EACH ROW EXECUTE FUNCTION "monitoring"."log_slow_query"();



CREATE OR REPLACE TRIGGER "update_documents_updated_at" BEFORE UPDATE ON "public"."documents" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at_column"();



ALTER TABLE ONLY "public"."documents"
    ADD CONSTRAINT "documents_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE CASCADE;



CREATE POLICY "Allow signup" ON "public"."users" FOR INSERT TO "anon" WITH CHECK (true);



CREATE POLICY "Service role has full access to documents" ON "public"."documents" TO "service_role" USING (true) WITH CHECK (true);



CREATE POLICY "Service role has full access to users" ON "public"."users" TO "service_role" USING (true) WITH CHECK (true);



CREATE POLICY "Users can insert own documents" ON "public"."documents" FOR INSERT TO "authenticated" WITH CHECK (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can read own documents" ON "public"."documents" FOR SELECT TO "authenticated" USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can read own record" ON "public"."users" FOR SELECT TO "authenticated" USING (("auth"."uid"() = "id"));



CREATE POLICY "Users can update own documents" ON "public"."documents" FOR UPDATE TO "authenticated" USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can update own record" ON "public"."users" FOR UPDATE TO "authenticated" USING (("auth"."uid"() = "id"));



CREATE POLICY "allow_signup" ON "public"."users" FOR INSERT TO "anon" WITH CHECK (true);



ALTER TABLE "public"."documents" ENABLE ROW LEVEL SECURITY;


CREATE POLICY "service_role_full_access" ON "public"."users" USING (true) WITH CHECK (true);



CREATE POLICY "user_read_own" ON "public"."users" FOR SELECT TO "authenticated" USING (("auth"."uid"() = "id"));



CREATE POLICY "user_update_own" ON "public"."users" FOR UPDATE TO "authenticated" USING (("auth"."uid"() = "id")) WITH CHECK (("auth"."uid"() = "id"));



ALTER TABLE "public"."users" ENABLE ROW LEVEL SECURITY;




ALTER PUBLICATION "supabase_realtime" OWNER TO "postgres";


GRANT USAGE ON SCHEMA "public" TO "postgres";
GRANT USAGE ON SCHEMA "public" TO "anon";
GRANT USAGE ON SCHEMA "public" TO "authenticated";
GRANT USAGE ON SCHEMA "public" TO "service_role";

























































































































































GRANT ALL ON FUNCTION "public"."update_updated_at_column"() TO "anon";
GRANT ALL ON FUNCTION "public"."update_updated_at_column"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."update_updated_at_column"() TO "service_role";


















GRANT ALL ON TABLE "public"."documents" TO "anon";
GRANT ALL ON TABLE "public"."documents" TO "authenticated";
GRANT ALL ON TABLE "public"."documents" TO "service_role";



GRANT ALL ON TABLE "public"."users" TO "anon";
GRANT ALL ON TABLE "public"."users" TO "authenticated";
GRANT ALL ON TABLE "public"."users" TO "service_role";









ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "service_role";






























RESET ALL;
