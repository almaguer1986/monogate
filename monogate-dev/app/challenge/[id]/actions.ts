"use server";

import { revalidatePath } from "next/cache";
import { supabase } from "@/lib/supabase";
import { validateExpression } from "@/lib/validate";

export interface SubmitResult {
  success: boolean;
  valid?: boolean;
  nodes?: number | null;
  depth?: number | null;
  error?: string | null;
  submissionId?: string;
}

export async function submitSolution(formData: FormData): Promise<SubmitResult> {
  const challengeId = (formData.get("challengeId") as string)?.trim();
  const author      = (formData.get("author")      as string)?.trim();
  const expression  = (formData.get("expression")  as string)?.trim();
  const notes       = (formData.get("notes")       as string)?.trim() || null;

  if (!challengeId || !author || !expression) {
    return { success: false, error: "Author and expression are required." };
  }

  if (author.length > 64) {
    return { success: false, error: "Author handle must be 64 characters or fewer." };
  }

  if (expression.length > 4000) {
    return { success: false, error: "Expression must be 4000 characters or fewer." };
  }

  // Validate
  const result = await validateExpression(challengeId, expression);

  // Store submission
  const { data: submission, error: insertError } = await supabase
    .from("submissions")
    .insert({
      challenge_id:     challengeId,
      author,
      expression,
      nodes:            result.nodes,
      depth:            result.depth,
      eml_calls:        result.eml_calls,
      valid:            result.valid,
      validation_error: result.valid ? null : result.error,
      notes,
    })
    .select("id")
    .single();

  if (insertError || !submission) {
    return { success: false, error: "Failed to store submission. Please try again." };
  }

  // Revalidate pages so leaderboard updates immediately
  revalidatePath(`/challenge/${challengeId}`);
  revalidatePath("/");

  return {
    success:      true,
    valid:        result.valid,
    nodes:        result.nodes,
    depth:        result.depth,
    error:        result.valid ? null : result.error,
    submissionId: submission.id,
  };
}
