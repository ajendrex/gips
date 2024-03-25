import React from 'react'
import {BrowserRouter as Router, Routes, Route} from 'react-router-dom'
import QuestionsPage from './QuestionsPage'
import {QueryClientProvider} from "react-query"
import {queryClient} from "./queryClient"

const App: React.FC = () => {
    return (
        <React.StrictMode>
            <QueryClientProvider client={queryClient}>
                <Router>
                    <Routes>
                        <Route path="/" element={<QuestionsPage/>}/>
                    </Routes>
                </Router>
            </QueryClientProvider>
        </React.StrictMode>
    )
}

export default App
