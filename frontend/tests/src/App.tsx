import React from 'react'
import {BrowserRouter as Router, Routes, Route} from 'react-router-dom'
import QuestionsPage from './pages/QuestionsPage'
import {QueryClientProvider} from "react-query"
import {queryClient} from "./provisions/queryClient"
import {ChakraBaseProvider} from "@chakra-ui/react";
import {theme} from "./provisions/chakraTheme";

const App: React.FC = () => {
    return (
        <React.StrictMode>
            <QueryClientProvider client={queryClient}>
                <ChakraBaseProvider theme={theme}>
                    <Router>
                        <Routes>
                            <Route path="/" element={<QuestionsPage/>}/>
                        </Routes>
                    </Router>
                </ChakraBaseProvider>
            </QueryClientProvider>
        </React.StrictMode>
    )
}

export default App
