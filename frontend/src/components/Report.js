import React from 'react';
import MarkdownView from 'react-showdown';

export default function Report({data}) {
    
    const markdown = `
        # Welcome to React Showdown :+1:

        To get started, edit the markdown in \`example/src/App.tsx\`.

        | Column 1 | Column 2 |
        |----------|----------|
        | A1       | B1       |
        | A2       | B2       |
    `;

    return (
        <div>
            <h2>Research Report</h2>
            <div id="reportContainer">
                <MarkdownView
                    markdown={markdown}
                    options={{ tables: true, emoji: true }}
                />
            </div>
        </div>
    );
};