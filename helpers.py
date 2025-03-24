
# Function to get the appropriate value index based on option dependency and state dependency
def get_value_index(parameter, option_index, iteration=None, actualFiniteSstateListShortName=None, actualStateShortName=None):
    """
    Get the appropriate value index based on option dependency and state dependency.
    
    Parameters:
    parameter: The parameter to get the value index for
    option_index (int): The index of the option to use for option-dependent parameters
    iteration: The iteration containing the ActualFiniteStateList (required for state-dependent parameters)
    actualFiniteStateListShortName (str, optional): The short name of the ActualFiniteStateList to use for state-dependent parameters
    actualStateShortName (str, optional): The short name of the specific ActualState to use
    
    Returns:
    int or None: The index of the value set to use, or None if an error occurred
    """
    # Handle parameters that are both option and state dependent
    if parameter.IsOptionDependent and parameter.StateDependence is not None:
        if iteration is None or actualFiniteStateListShortName is None:
            print(f"ERROR: Parameter {parameter.UserFriendlyShortName} is both option and state dependent, but state information is missing.")
            return None
        
        # If no specific state is provided, we can't proceed
        if actualStateShortName is None:
            print(f"ERROR: Parameter {parameter.UserFriendlyShortName} is state dependent, but no specific state was provided.")
            return None
        for stateList in iteration.ActualFiniteStateList:
            if stateList.UserFriendlyShortName == actualFiniteStateListShortName:
                n_states = stateList.ActualState.Count
                break
        # Directly find the value set with the matching state and option
        for i, value_set in enumerate(parameter.ValueSet):
            if value_set.ActualState is not None and value_set.ActualState.UserFriendlyShortName == actualStateShortName and value_set.ActualOption is not None and value_set.ActualOption.UserFriendlyShortName == iteration.Option[option_index].ShortName:
                return i

        print(f"ERROR: Could not find ValueSet for parameter {parameter.UserFriendlyShortName} with state {actualStateShortName} and option index {option_index}")
        return None
            
    # Handle parameters that are only option dependent
    elif parameter.IsOptionDependent:
        for i, value_set in enumerate(parameter.ValueSet):
            if value_set.ActualOption is not None and value_set.ActualOption.UserFriendlyShortName == iteration.Option[option_index].ShortName:
                return i
        
    # Handle parameters that are only state dependent
    elif parameter.StateDependence is not None:
        if iteration is None or actualFiniteStateListShortName is None:
            print(f"ERROR: Parameter {parameter.UserFriendlyShortName} is state dependent, but state information is missing.")
            return None
            
        # If no specific state is provided, we can't proceed
        if actualStateShortName is None:
            print(f"ERROR: Parameter {parameter.UserFriendlyShortName} is state dependent, but no specific state was provided.")
            return None
            
        # Directly find the value set with the matching state
        for i, value_set in enumerate(parameter.ValueSet):
            if value_set.ActualState is not None and value_set.ActualState.UserFriendlyShortName == actualStateShortName:
                return i
                    
        print(f"ERROR: Could not find ValueSet for parameter {parameter.UserFriendlyShortName} with state {actualStateShortName}")
        return None

    # Parameter is neither option nor state dependent
    else:
        return 0


def update_element_parameter(iteration, element_definition, param_suffix, option_index, computed_value, actualFiniteStateListShortName=None, actualStateShortName=None):
    """
    Find a parameter by its suffix in an element definition and update its value.
    
    Parameters:
    iteration: The iteration context
    element_definition: The element definition containing the parameter
    param_suffix (str): The suffix of the parameter to update (e.g., 'm', 'P_mean')
    option_index (int): The index of the option to use for option-dependent parameters
    computed_value: The new value to set
    actualFiniteStateListShortName (str, optional): The short name of the ActualFiniteStateList to use for state-dependent parameters
    actualStateShortName (str, optional): The short name of the specific ActualState to use
    
    Returns:
    bool: True if the parameter was found and updated, False otherwise
    """
    # Import required references
    import clr
    clr.AddReference("CDP4Dal")
    from CDP4Dal import Operations
    from CDP4Common.EngineeringModelData import ParameterSwitchKind
    
    # Find the parameter by its suffix
    param_name = f"{element_definition.UserFriendlyShortName}.{param_suffix}"
    for parameter in element_definition.Parameter:
        if parameter.UserFriendlyShortName == param_name:
            # Get the value set for this option
            value_index = get_value_index(parameter, option_index, iteration, actualFiniteStateListShortName, actualStateShortName)
            if value_index is None:
                print(f"ERROR: Failed to get value index for parameter {param_name}")
                return False
            elif not parameter.IsOptionDependent:
                if iteration.DefaultOption != iteration.Option[option_index]:
                    print(f"ERROR: Parameter {parameter.UserFriendlyShortName} is not option dependent, but option index {option_index} does not match default option index.")
                    return False
            elif not parameter.StateDependence and actualFiniteStateListShortName is None:
                if iteration.ActualFiniteStateList is None or actualFiniteStateListShortName is None:
                    print(f"ERROR: Parameter {parameter.UserFriendlyShortName} is not state dependent, but no state information was provided.")
                    return False
            if value_index < len(parameter.ValueSet):
                value_set = parameter.ValueSet[value_index]
                
                # Check if update is needed
                current_value = value_set.ActualValue[0] if value_set.ActualValue else "-"
                if current_value == "-" or safe_float(current_value) != computed_value:
                    # Update the parameter value
                    transactionContext = Operations.TransactionContextResolver.ResolveContext(iteration)
                    updateTransaction = Operations.ThingTransaction(transactionContext)
                    
                    # Clone the value set and update it
                    clonedValuesSet = value_set.Clone(False)
                    clonedValuesSet.SetValue("computed", str(computed_value))
                    clonedValuesSet.SetValue("valueSwitch", ParameterSwitchKind.COMPUTED)
                    value_set.ResetComputed()
                    
                    # Add the update to the transaction and finalize
                    updateTransaction.CreateOrUpdate(clonedValuesSet)
                    updateOperationContainer = updateTransaction.FinalizeTransaction()
                    
                    # Write the changes to the session
                    Command.ScriptingPanelViewModel.SelectedSession.Write(updateOperationContainer)

                    print(f"\nUpdated {element_definition.UserFriendlyName} {param_suffix} to {computed_value:.4f}\n")
                    return True
                else:
                    print(f"\n{element_definition.UserFriendlyName} {param_suffix} is already {computed_value:.4f}\n")
                    return True
            else:
                print(f"ERROR: Value index {value_index} is out of range for parameter {param_name}")
                return False
    
    print(f"Parameter with suffix '{param_suffix}' not found in {element_definition.UserFriendlyName}")
    return False