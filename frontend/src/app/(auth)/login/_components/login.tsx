"use client";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Form } from "@/components/ui/form";
import { LoginForm, LoginSchemaForm } from "@/validations/auth-validation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { INITIAL_LOGIN_FORM } from "@/constants/auth-constant";
import { Button } from "@/components/ui/button";
import FormInput from "@/components/common/form-input";
import { useLogin } from "@/hooks/auth/use-auth";

export default function Login() {
  const { mutate: login, isPending: isLoginLoading } = useLogin();

  const form = useForm<LoginForm>({
    resolver: zodResolver(LoginSchemaForm),
    defaultValues: INITIAL_LOGIN_FORM,
  });

  const onSubmit = form.handleSubmit((data) => {
    login(data);
  });

  return (
    <Card>
      <CardHeader className="text-center">
        <CardTitle className="text-xl font-medium">Welcome</CardTitle>
        <CardDescription>Login to your account</CardDescription>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={onSubmit} className="space-y-4">
            <FormInput
              form={form}
              name="email"
              label="Email"
              placeholder="Enter email here"
              type="email"
            />
            <FormInput
              form={form}
              name="password"
              label="Password"
              placeholder="••••••"
              type="password"
            />
            <Button type="submit" disabled={isLoginLoading}>
              Login
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
