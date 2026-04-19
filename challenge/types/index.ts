export type ChallengeStatus = "open" | "solved" | "closed";

export interface Challenge {
  id: string;
  name: string;
  description: string;
  status: ChallengeStatus;
  grammar: string;
  best_known_nodes: number | null;
  best_known_depth: number | null;
  best_submission_id: string | null;
  created_at: string;
  submission_count?: number;
  best_author?: string | null;
}

export interface Submission {
  id: string;
  challenge_id: string;
  author: string;
  expression: string;
  nodes: number | null;
  depth: number | null;
  eml_calls: number | null;
  valid: boolean;
  validation_error: string | null;
  notes: string | null;
  created_at: string;
}

export interface SubmissionWithChallenge extends Submission {
  challenges: { id: string; name: string } | null;
}
