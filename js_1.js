/////////// при изменении одного поля - отображать эти данные в другом

"use client"
import {useEffect, useState} from "react";
import {Controller, useForm} from "react-hook-form";
import {TextField} from "@mui/material";


export function ReusableComponent({control, name, label, type, required, errors, endPoint}) {

    let errorField = errors?.[name]


    return (
        <>
            <Controller

                // обязательные аргументы начало
                control={control}
                name={name}
                defaultValue=""
                // обязательные аргументы конец

                rules={{
                    maxLength: {
                        value: 50,
                        message: "Имя не может быть длиннее 50 символов"
                    }
                }}

                render={({field}) => {

                    return <TextField
                        // обязательные аргументы начало
                        {...field}
                        // обязательные аргументы конец

                        type={type}
                        error={!!errorField}
                        helperText={errorField?.message || ""}
                        id={name}
                        label={label}
                        variant={'outlined'}
                        required={required}
                    />
                }}
            >
            </Controller>
        </>
    )

}


export default function TestComponent() {

    let {
        control, handleSubmit,
        reset, watch, setValue, formState: {errors}
    } = useForm({
        mode: "onChange",
    });

    // следим за значением первого поля
    let firstFieldValue = watch("first_input")

    // при изменении значения в первом поле - меняем значение второго
    useEffect(() => {
        setValue("second_input", firstFieldValue)
    }, [firstFieldValue])

    return (

        <form>
            <ReusableComponent
                control={control}
                type="text"
                name='first_input'
                label={"First"}
                errors={errors}
                required={false}
            ></ReusableComponent>


            <ReusableComponent
                control={control}
                type="text"
                name='second_input'
                label={"Second"}
                errors={errors}
                required={false}
            ></ReusableComponent>

        </form>

    );
}
