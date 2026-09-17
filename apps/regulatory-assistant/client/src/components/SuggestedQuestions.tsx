/**
 * SuggestedQuestions.tsx
 * Pre-loaded question chips for cold-start on the Ask screen.
 * Questions are grounded in FCC 26-19 corrected facts.
 */
import { SUGGESTED_QUESTIONS } from '../mock/mockData';

interface SuggestedQuestionsProps {
  onSelect: (question: string) => void;
}

export function SuggestedQuestions({ onSelect }: SuggestedQuestionsProps) {
  return (
    <div className="flex flex-wrap gap-2 justify-center max-w-2xl mx-auto">
      {SUGGESTED_QUESTIONS.map((q) => (
        <button
          key={q}
          onClick={() => onSelect(q)}
          className="px-3 py-1.5 text-xs border rounded-full hover:bg-primary hover:text-primary-foreground transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FF3621]"
        >
          {q}
        </button>
      ))}
    </div>
  );
}
