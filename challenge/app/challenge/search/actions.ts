"use server";

import { revalidatePath } from "next/cache";
import { supabase } from "@/lib/supabase";
import { validateExpression } from "@/lib/validate";

export interface AutoSubmitResult {
  success: boolean;
  valid?: boolean;
  nodes?: number | null;
  depth?: number | null;
  error?: string | null;
  submissionId?: string;
}

export async function autoSubmit(
  challengeId: string,
  expression: string
): Promise<AutoSubmitResult> {
  if (!challengeId || !expression) {
    return { success: false, error: "Missing challengeId or expression." };
  }

  if (expression.length > 4000) {
    return { success: false, error: "Expression exceeds 4000 characters." };
  }

  const result = await validateExpression(challengeId, expression);

  const { data: submission, error: insertError } = await supabase
    .from("submissions")
    .insert({
      challenge_id:     challengeId,
      author:           "search-bot",
      expression,
      nodes:            result.nodes,
      depth:            result.depth,
      eml_calls:        result.eml_calls,
      valid:            result.valid,
      validation_error: result.valid ? null : result.error,
      notes:            "Found automatically by the EML symbolic regression search tool (gradient descent).",
    })
    .select("id")
    .single();

  if (insertError || !submission) {
    return { success: false, error: "Failed to store submission." };
  }

  revalidatePath(`/challenge/${challengeId}`);
  revalidatePath("/");
  revalidatePath("/leaderboard");

  return {
    success:      true,
    valid:        result.valid,
    nodes:        result.nodes,
    depth:        result.depth,
    error:        result.valid ? null : result.error,
    submissionId: submission.id,
  };
}
