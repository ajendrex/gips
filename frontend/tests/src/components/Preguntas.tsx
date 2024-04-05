import {PreguntaLikertNOAS, RespuestaParams} from "../interfaces";
import React, {useEffect, useRef, useState} from "react";
import {useMutation} from "react-query";
import {
    Box,
    Button,
    Card,
    FormControl,
    FormLabel,
    Heading,
    Radio,
    RadioGroup,
    Stack,
    Switch,
    Text
} from "@chakra-ui/react";
import axios from "axios";
import {getCsrfToken} from "../csrf";

const submitRespuesta = async ({codigo, idPregunta, respuesta}: RespuestaParams): Promise<void> => {
    const result = await axios.post(
        `/api/tests/respuestas-likert-noas/?codigo=${codigo}`,
        {
            pregunta: idPregunta,
            alternativa: respuesta,
        },
        {
            headers: {
                'X-CSRFToken': getCsrfToken(),
            }
        }
    )
    if (result.status !== 201) {
        throw new Error(`Error al enviar la respuesta: ${result.data}`)
    }
}

export const Preguntas = ({preguntas, codigo}: {preguntas: PreguntaLikertNOAS[], codigo: string}) => {
    const [autoScroll, setAutoScroll] = useState(true)
    const [respuestas, setRespuestas] = useState<{ [preguntaId: number]: string }>({})
    const preguntaRefs = useRef<(HTMLDivElement | null)[]>([])
    const [preguntaEnFoco, setPreguntaEnFoco] = useState<number | null>(null)

    const mutation = useMutation(({codigo, idPregunta, respuesta}: RespuestaParams) => submitRespuesta({
        codigo,
        idPregunta,
        respuesta
    }))

    useEffect(() => {
        if (preguntaRefs.current[0]) {
            setPreguntaEnFoco(preguntas[0].id)
        }
    }, [preguntas, preguntaRefs])

    const observarScroll = () => {
        const alturaTotalDocumento = document.documentElement.scrollHeight
        const alturaViewport = window.innerHeight
        const maxScrollY = alturaTotalDocumento - alturaViewport
        const alturaPorPregunta = maxScrollY / (preguntas.length || 1)
        // Calcula el índice de la pregunta basado en el scroll actual
        const indicePreguntaEnFoco = Math.floor(window.scrollY / alturaPorPregunta)

        console.log(`h_total: ${alturaTotalDocumento}, viewPort: ${alturaViewport}, alturaPorPregunta: ${alturaPorPregunta}, maxScrolY: ${maxScrollY} scrollY: ${window.scrollY}, indicePregunta: ${indicePreguntaEnFoco}`)

        // Asegura que el índice está dentro de los límites del array de preguntas
        if (indicePreguntaEnFoco >= 0 && indicePreguntaEnFoco < (preguntas.length || 0)) {
            const preguntaId = preguntas[indicePreguntaEnFoco].id
            setPreguntaEnFoco(preguntaId || null)
        }
    }

    useEffect(() => {
        window.addEventListener('scroll', observarScroll)

        return () => {
            window.removeEventListener('scroll', observarScroll)
        }
    }, [preguntas])

    const handleAnswerSelect = (idPregunta: number, respuesta: string) => {
        const nuevasRespuestas = {...respuestas, [idPregunta]: respuesta}
        setRespuestas(nuevasRespuestas)

        mutation.mutate({codigo, idPregunta, respuesta})

        if (autoScroll) {
            const siguientePreguntaIndex = preguntas.findIndex(
                pregunta => !nuevasRespuestas[pregunta.id]
            )
            enfocarPregunta(siguientePreguntaIndex)
        }
    }

    const enfocarPregunta = (index: number) => {
        const alturaTotalDocumento = document.documentElement.scrollHeight
        const alturaViewport = window.innerHeight
        const maxScrollY = alturaTotalDocumento - alturaViewport

        if (index === -1) {
            window.scrollTo({top: maxScrollY, behavior: 'smooth'})
        } else if (autoScroll) {
            const alturaPorPregunta = maxScrollY / (preguntas.length || 1)

            // Calcula el nuevo scrollY basado en el índice de la pregunta
            const nuevoScrollY = alturaPorPregunta * index + alturaPorPregunta / 2

            // Mueve el scroll a la posición calculada
            window.scrollTo({top: nuevoScrollY, behavior: 'smooth'})
        } else if (index < preguntaRefs.current.length) {
            setPreguntaEnFoco(preguntas[index].id)
        }
    }

    return (
        <>
            <Box position="fixed" bottom="20px" right="20px" zIndex="1000">
                <FormControl display="flex" alignItems="center">
                    <FormLabel htmlFor="auto-scroll" mb="0" mr="2">
                        Auto-scroll
                    </FormLabel>
                    <Switch id="auto-scroll" isChecked={autoScroll} onChange={() => setAutoScroll(!autoScroll)} />
                </FormControl>
            </Box>
            <Box h={300} />
            {

                preguntas.map((pregunta, index) => (
                    <Box
                        key={pregunta.id}
                        ref={el => preguntaRefs.current[index] = el}
                        padding="20px"
                        mb="4"
                        boxShadow="lg"
                        borderRadius="md"
                        opacity={preguntaEnFoco === pregunta.id ? 1 : 0.5}
                        onClick={() => enfocarPregunta(index)}
                    >
                        <Box
                            h={150}
                            display="flex"
                            flexDirection="column"
                            justifyContent="center"
                        >
                            <Text
                                align="center"
                                fontWeight="bold"
                                fontFamily="'Roboto Slab', serif"
                                opacity={preguntaEnFoco === pregunta.id ? 1 : 0.5}
                            >{pregunta.texto}</Text>
                        </Box>
                        <RadioGroup onChange={(value) => handleAnswerSelect(pregunta.id, value)} value={respuestas[pregunta.id]}>
                            <Stack direction="column">
                                {[
                                    {text: "Rara vez o nunca", code: "N"},
                                    {text: "Ocasionalmente", code: "O"},
                                    {text: "A menudo", code: "A"},
                                    {text: "Siempre o casi siempre", code: "S"},
                                ].map(({text, code}) => (
                                    <Radio
                                        key={code}
                                        value={code}
                                        opacity={preguntaEnFoco === pregunta.id ? 1 : 0.5}
                                    >
                                        {text}
                                    </Radio>
                                ))}
                            </Stack>
                        </RadioGroup>
                    </Box>
                ))
            }
            <Box h={300}>
                {
                    Object.keys(respuestas).length === preguntas.length && (
                        <Card p="10px">
                            <Box
                                display="flex"
                                justifyContent="center"
                                alignItems="center"
                                flexDirection="column"
                            >
                                <Stack spacing="30px">
                                    <Heading size="sm" mb="10px" mt="50px" textAlign="center">
                                        ¡Perfecto!<br />
                                    </Heading>
                                    <Text lineHeight="25px">
                                        Ahora debes agendar una entrevista con el psicólogo en el siguiente paso.
                                    </Text>
                                    <Box display="flex" justifyContent="center" mb="10px">
                                        <Button
                                            colorScheme="teal"
                                            onClick={() => {/* Ir a la siguiente página */}}
                                        >
                                            Agendar Llamada
                                        </Button>
                                    </Box>
                                </Stack>
                            </Box>
                        </Card>
                    )
                }
            </Box>
        </>
    )
}
