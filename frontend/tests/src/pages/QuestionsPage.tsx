import React, {useState} from 'react'
import {useQuery} from 'react-query'
import {useLocation} from 'react-router-dom'
import axios from "axios"
import {Prueba} from "../interfaces"
import {Box, Button, Card, Heading, Stack, Text} from "@chakra-ui/react"
import {Preguntas} from "../components/Preguntas";

const fetchPrueba = async (codigo: string): Promise<Prueba> => {
    const resp = await axios.get(`/api/tests/tests/?codigo=${codigo}`)
    if (resp.status !== 200) {
        throw new Error(`Error al obtener las preguntas: ${resp.data}`)
    }
    return resp.data
}

function useQueryParams() {
    return new URLSearchParams(useLocation().search)
}

const QuestionsPage: React.FC = () => {
    const queryParams = useQueryParams()
    const codigo = queryParams.get('codigo') || ''
    const [introAceptada, setIntroAceptada] = useState<boolean>(false)

    const {data: prueba, isLoading, error} = useQuery(['fetchPrueba', codigo], () => fetchPrueba(codigo))

    return (
        <div style={{display: "flex", justifyContent: "center", alignItems: "center", minHeight: "100vh", padding: "20px"}}>
            <Box width="100%" maxW="500px">
                {isLoading ? (
                    <div>Cargando...</div>
                ) : error ? (
                    <div>Ocurrió un error al cargar las preguntas</div>
                ) : introAceptada ? (
                    <Preguntas preguntas={prueba!.preguntalikertnoas_set} codigo={codigo} />
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

export default QuestionsPage
