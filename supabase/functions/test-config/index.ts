import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { edgeConfig } from '../../../shared/environment';

serve(async (req) => {
  const env = {
    environment: Deno.env.get('ENV_LEVEL'),
    isEdgeFunction: true,
    vectorProcessingEnabled: edgeConfig.enableVectorProcessing,
    regulatoryProcessingEnabled: edgeConfig.enableRegulatoryProcessing,
    logLevel: edgeConfig.logLevel
  };

  return new Response(
    JSON.stringify(env),
    { headers: { "Content-Type": "application/json" } }
  );
}); 