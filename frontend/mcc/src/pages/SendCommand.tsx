import { useState, type FormEvent } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faSpinner } from "@fortawesome/free-solid-svg-icons";
import { Button } from "@/components/ui/button";
import {
  Field,
  FieldDescription,
  FieldGroup,
  FieldLabel,
  FieldLegend,
  FieldSet,
} from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import CustomAlert from "@/components/Alert";
import type { MainCommand } from "../utils/types";
import { parseCommandParameters, type CommandParameter } from "../utils/commandParams";
import { createCommand } from "../utils/api/commands";
import { ApiError } from "../utils/api/auth";
import { isSessionLockedOut } from "../utils/lockout";

interface ParameterValues {
  [key: string]: string;
}

const SubmitStatus = {
  None: "NONE",
  Success: "SUCCESS",
  InvalidForm: "INVALID_FORM",
  LockedOut: "LOCKED_OUT",
  UnknownError: "UNKNOWN_ERROR",
} as const;

type SubmitStatus = (typeof SubmitStatus)[keyof typeof SubmitStatus];

const submitAlerts: Record<
  SubmitStatus,
  { destructive: boolean; title: string; description: string; timeout?: number | null }
> = {
  [SubmitStatus.None]: { destructive: false, title: "", description: "" },
  [SubmitStatus.Success]: {
    destructive: false,
    title: "Success, command submitted!",
    description: "",
    timeout: 7000,
  },
  [SubmitStatus.InvalidForm]: {
    destructive: true,
    title: "Form invalid. Please fill in all required fields with valid values.",
    description: "",
    timeout: null,
  },
  [SubmitStatus.LockedOut]: {
    destructive: true,
    title: "Session is locked; commands can't be scheduled this close to session start.",
    description: "",
    timeout: null,
  },
  [SubmitStatus.UnknownError]: {
    destructive: true,
    title: "An unknown error occurred. Please try again.",
    description: "",
    timeout: null,
  },
};

/**
 * @brief SendCommand component for displaying and submitting command parameters
 * @return tsx element of SendCommand component
 */
function SendCommand({
  mainCommand,
  selectedSessionId,
  sessionStartTime,
  setSelectedCommandId,
  onSubmitted,
}: {
  mainCommand: MainCommand | null;
  selectedSessionId: string | null;
  sessionStartTime: string | null;
  setSelectedCommandId: (id: number | null) => void;
  onSubmitted: () => void;
}) {
  const [parameterValues, setParameterValues] = useState<ParameterValues>({});
  const [sequenceIndex, setSequenceIndex] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [currentSubmitStatus, setCurrentSubmitStatus] = useState<SubmitStatus>(SubmitStatus.None);

  const parameters: CommandParameter[] = mainCommand ? parseCommandParameters(mainCommand) : [];
  const lockedOut = sessionStartTime ? isSessionLockedOut(sessionStartTime) : false;

  const handleParameterChange = (paramName: string, value: string) => {
    setParameterValues((prev) => ({ ...prev, [paramName]: value }));
  };

  // TODO: replace with command-specific validation
  const validateParameter = (param: CommandParameter, value: string): boolean => {
    if (!value.trim()) return false;

    switch (param.type) {
      case "int":
        return !isNaN(parseInt(value, 10));
      case "float":
        return !isNaN(parseFloat(value));
      case "boolean":
        return value.toLowerCase() === "true" || value.toLowerCase() === "false";
      default:
        return true;
    }
  };

  const isFormValid = (): boolean => {
    if (!mainCommand) return false;
    return parameters.every((param) => validateParameter(param, parameterValues[param.name] || ""));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!mainCommand || !selectedSessionId || !isFormValid()) {
      setCurrentSubmitStatus(SubmitStatus.InvalidForm);
      return;
    }
    if (lockedOut) {
      setCurrentSubmitStatus(SubmitStatus.LockedOut);
      return;
    }

    setCurrentSubmitStatus(SubmitStatus.None);
    setIsSubmitting(true);

    try {
      const paramsString = parameters.length
        ? parameters.map((p) => parameterValues[p.name]).join(",")
        : undefined;

      await createCommand({
        type_: mainCommand.id,
        params: paramsString,
        session_id: selectedSessionId,
        sequence_index: sequenceIndex.trim() ? parseInt(sequenceIndex, 10) : undefined,
      });

      setCurrentSubmitStatus(SubmitStatus.Success);
      setParameterValues({});
      setSequenceIndex("");
      onSubmitted();
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) {
        setCurrentSubmitStatus(SubmitStatus.LockedOut);
      } else {
        setCurrentSubmitStatus(SubmitStatus.UnknownError);
      }
      console.error("Error submitting command:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderParameterInput = (param: CommandParameter) => {
    const value = parameterValues[param.name] || "";
    const isValid = validateParameter(param, value);
    const inputId = `param-${param.name}`;

    const baseInputClasses = `
      w-full px-3 py-2 border rounded-md
      focus:outline-none focus:ring-2 focus:ring-blue-500
      ${!isValid && value ? "border-red-500 bg-red-50" : "border-gray-300"}
    `;

    switch (param.type) {
      case "boolean":
        return (
          <Select value={value} onValueChange={(val) => handleParameterChange(param.name, val)}>
            <SelectTrigger
              className={`w-[180px] ${!isValid && value ? "border-red-500 bg-red-50" : "border-gray-300"}`}
            >
              <SelectValue placeholder="Select..." />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="true">True</SelectItem>
              <SelectItem value="false">False</SelectItem>
            </SelectContent>
          </Select>
        );

      case "int":
      case "float":
        return (
          <Input
            id={inputId}
            type="number"
            value={value}
            onChange={(e) => handleParameterChange(param.name, e.target.value)}
            className={baseInputClasses}
            placeholder={param.type === "int" ? "Enter integer" : "Enter decimal number"}
            step={param.type === "float" ? "any" : "1"}
          />
        );

      default:
        return (
          <Input
            id={inputId}
            type="text"
            value={value}
            onChange={(e) => handleParameterChange(param.name, e.target.value)}
            className={baseInputClasses}
            placeholder="Enter text"
          />
        );
    }
  };

  if (!mainCommand) {
    return null;
  }

  return (
    <div className="p-4 space-y-6 bg-card w-96 border rounded-md animate-in zoom-in-75 duration-300 slide-in-from-left-10">
      {currentSubmitStatus !== SubmitStatus.None && (
        <CustomAlert
          destructive={submitAlerts[currentSubmitStatus].destructive}
          title={submitAlerts[currentSubmitStatus].title}
          description={submitAlerts[currentSubmitStatus].description}
          timeout={submitAlerts[currentSubmitStatus].timeout}
        />
      )}
      <form onSubmit={handleSubmit}>
        <FieldGroup>
          <FieldSet>
            <FieldLegend>{mainCommand.name}</FieldLegend>
            <FieldDescription>
              Command ID: {mainCommand.id} | Data Size: {mainCommand.data_size} | Total Size:{" "}
              {mainCommand.total_size} bytes
            </FieldDescription>
            <FieldGroup>
              {parameters.map((param) => {
                const value = parameterValues[param.name] || "";
                const isValid = validateParameter(param, value);
                return (
                  <Field key={param.name}>
                    <FieldLabel htmlFor={`param-${param.name}`}>{param.name}</FieldLabel>
                    {renderParameterInput(param)}
                    <div
                      className="transition-all duration-300 overflow-hidden"
                      style={{ maxHeight: !isValid && value ? "3rem" : "0" }}
                    >
                      {!isValid && value && (
                        <p className="text-sm text-red-600 animate-in fade-in-50 duration-150">
                          Invalid {param.type} value
                        </p>
                      )}
                    </div>
                  </Field>
                );
              })}
            </FieldGroup>
          </FieldSet>
          <Field>
            <FieldLabel htmlFor="sequence-index">Sequence index (optional)</FieldLabel>
            <Input
              id="sequence-index"
              type="number"
              value={sequenceIndex}
              onChange={(e) => setSequenceIndex(e.target.value)}
              placeholder="e.g. 0, 1, 2..."
            />
          </Field>
          <Field orientation="horizontal">
            <Button type="submit" disabled={!isFormValid() || isSubmitting}>
              Submit
              {isSubmitting && <FontAwesomeIcon icon={faSpinner} className="animate-spin" />}
            </Button>
            <Button
              variant="outline"
              type="button"
              onClick={() => setSelectedCommandId(null)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
          </Field>
        </FieldGroup>
      </form>
    </div>
  );
}

export default SendCommand;
