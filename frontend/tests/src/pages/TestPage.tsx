import React, {useEffect, useState} from 'react'
import {useQuery} from 'react-query'
import {useLocation} from 'react-router-dom'
import axios from "axios"
import {Prueba} from "../interfaces"
import {
    Alert, AlertDescription,
    AlertIcon,
    AlertTitle,
    Box,
    Button,
    Card, CloseButton,
    Heading,
    Spinner,
    Stack,
    Text,
    useToast
} from "@chakra-ui/react"
import {Preguntas} from "../components/Preguntas";
import Agenda from "../components/Agenda";

const fetchPrueba = async (codigo: string): Promise<Prueba> => {
    try {
        const resp = await axios.get(`/api/tests/tests/?codigo=${codigo}`)
        return resp.data
    } catch (error: any) {
        const errorMsg = error.response.data[0] || error.response.data.detail || "Algo salió mal"
        throw new Error(errorMsg)
    }
}

function useQueryParams() {
    return new URLSearchParams(useLocation().search)
}

const TestPage: React.FC = () => {
    const queryParams = useQueryParams()
    const codigo = queryParams.get('codigo') || ''
    const [introAceptada, setIntroAceptada] = useState<boolean>(false)
    const [preguntasRespondidas, setPreguntasRespondidas] = useState<boolean>(false)
    const [entrevistaAgendada, setEntrevistaAgendada] = useState<boolean>(false)
    const [terminado, setTerminado] = useState<boolean>(false)

    const terminar = () => {
        window.close()
        setTerminado(true)
    }

    const {data: prueba, isLoading, error} = useQuery<Prueba, Error>(
        ['fetchPrueba', codigo],
        () => fetchPrueba(codigo),
        {refetchOnWindowFocus: false}
        )

    const itemsAlignment = preguntasRespondidas ? "start" : "center"

    return (
        <div style={{display: "flex", justifyContent: "center", alignItems: itemsAlignment, minHeight: "100vh", padding: "20px"}}>
            <Box width="100%" maxW="500px">
                {isLoading ? (
                    <Spinner speed="1s" />
                ) : error ? (
                    <Alert status="error">
                        <AlertIcon />
                        <AlertTitle>Error</AlertTitle>
                        <AlertDescription>{error.message}</AlertDescription>
                    </Alert>
                ) : terminado ? (
                    <Card p="10px">
                        <Text>Ya puedes cerrar tu navegador manualmente, nosotros lo intentamos pero no se pudo.</Text>
                    </Card>
                ) : entrevistaAgendada ? (
                        <Card p="10px">
                            <Alert status="success">
                                <AlertDescription>La entrevista ha sido agendada con éxito.</AlertDescription>
                                <CloseButton position="absolute" right="8px" top="8px" onClick={terminar}/>
                            </Alert>
                        </Card>
                ) : preguntasRespondidas ? (
                    <Card p="10px">
                        <Agenda codigo={codigo} successCallback={() => setEntrevistaAgendada(true)} />
                    </Card>
                ) : introAceptada ? (
                    <Preguntas preguntas={prueba!.preguntalikertnoas_set} codigo={codigo} successCallback={() => setPreguntasRespondidas(true)} />
                ) : (
                    <Card p="10px">
                        <Stack spacing="15px">
                            <Box mb="30px">
                                <Heading size="lg" textAlign="center">Test de control de los impulsos</Heading>
                            </Box>
                            <Text>Hola!</Text>
                            <Text>Bienvenido(a) a esta evaluación online.</Text>
                            <Text>A continuación leerás una serie de oraciones con alternativas de respuesta.</Text>
                            <Text>En cada caso selecciona aquella que más te represente, sin pensarlo demasiado.</Text>
                            <Box display="flex" justifyContent="center">
                                <Button colorScheme="teal" onClick={() => setIntroAceptada(true)}>Aceptar</Button>
                            </Box>
                        </Stack>
                    </Card>
                )}
            </Box>
        </div>
    )
}

export default TestPage
