"use client";

import React from "react";

/**
 * FormattedText parses a plain text string and renders it with basic markdown-style 
 * formatting, specifically supporting unordered lists (bullets) and line breaks.
 */
export function FormattedText({ 
  text, 
  className = "" 
}: { 
  text: string | null | undefined;
  className?: string;
}) {
  if (!text) return null;

  // Split text into lines
  const lines = text.split("\n");
  const elements: React.ReactNode[] = [];
  let currentList: React.ReactNode[] = [];

  const flushList = () => {
    if (currentList.length > 0) {
      elements.push(
        <ul key={`list-${elements.length}`} className="my-3 list-disc space-y-1.5 pl-6">
          {currentList}
        </ul>
      );
      currentList = [];
    }
  };

  lines.forEach((line, index) => {
    const trimmedLine = line.trim();
    
    // Check if line starts with a bullet marker: "- ", "* ", or "• "
    const isBullet = trimmedLine.startsWith("- ") || 
                     trimmedLine.startsWith("* ") || 
                     trimmedLine.startsWith("• ");

    if (isBullet) {
      // Remove the marker and create a list item
      const content = trimmedLine.substring(2).trim();
      currentList.push(
        <li key={`li-${index}`} className="text-inherit leading-relaxed">
          {content}
        </li>
      );
    } else {
      // If we were in a list, finish it
      flushList();

      if (trimmedLine === "") {
        // Empty lines act as spacers
        elements.push(<div key={`spacer-${index}`} className="h-2" />);
      } else {
        // Normal paragraph
        elements.push(
          <p key={`p-${index}`} className="text-inherit leading-relaxed">
            {line}
          </p>
        );
      }
    }
  });

  // Flush any remaining list
  flushList();

  return <div className={`space-y-1 ${className}`}>{elements}</div>;
}
