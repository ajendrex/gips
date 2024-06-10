import React from 'react'
import {BrowserRouter as Router, Routes, Route} from 'react-router-dom'
import TestPage from './pages/TestPage'
import {QueryClientProvider} from "react-query"
import {queryClient} from "./provisions/queryClient"
import {ChakraBaseProvider} from "@chakra-ui/react";
import {theme} from "./provisions/chakraTheme";

const App: React.FC = () => {
    return (
        <React.StrictMode>
            <QueryClientProvider client={queryClient}>
                <ChakraBaseProvider theme={theme}>
                    <Router basename="/tests/">
                        <Routes>
                            <Route path="/" element={<TestPage/>}/>
                        </Routes>
                    </Router>
                </ChakraBaseProvider>
            </QueryClientProvider>
        </React.StrictMode>
    )
}

export default App
