import React, {useEffect, useState} from 'react'
import {marked} from "marked";
import styled from "@emotion/styled"

const MarkdownContent = styled.div` 
    h1, h2, h3 {
        color: #2377bc;
    }
    
    h1 {
        font-size: 24px;
        text-align: center;
    } 
    h2 {
        font-size: 20px;
    } 
    h3 {
        font-size: 16px;
    }
    p, ol {
        margin: revert;
        padding: revert;
    }
    a {
        color: revert;
    }
`;

const MarkdownRenderer = ({ url }: {url: string}) => {
    const [markdownText, setMarkdownText] = useState('')

    useEffect(() => {
        fetch(url)
            .then(response => response.text())
            .then(text => setMarkdownText(marked.parse(text) as string))
            .catch(error => console.error('Error loading the markdown file: ', error))
    }, [url])

    return <MarkdownContent dangerouslySetInnerHTML={{ __html: markdownText}} />
}

export default MarkdownRenderer
